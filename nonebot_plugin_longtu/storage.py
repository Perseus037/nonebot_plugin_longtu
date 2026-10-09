from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import time
import uuid
from contextlib import asynccontextmanager, suppress
from functools import partial
from pathlib import Path

import httpx
from loguru import logger

BASE_URL = "https://raw.githubusercontent.com/Whiked/Dragonimg/main/drimg/"
MAX_BYTES = 20 * 1024 * 1024
NAME_RE = re.compile(r"[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|gif|webp)", re.I)


async def offload(func, *args):
    return await asyncio.get_running_loop().run_in_executor(None, partial(func, *args))


def image_header(data):
    return (
        data.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a"))
        or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
    )


def valid_entry(name, entry):
    return (
        isinstance(name, str) and NAME_RE.fullmatch(name)
        and isinstance(entry, dict)
        and type(entry.get("size")) is int and 0 < entry["size"] <= MAX_BYTES
        and isinstance(entry.get("sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", entry["sha"])
    )


def read_index(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data or not all(valid_entry(k, v) for k, v in data.items()):
        raise ValueError("Invalid image index")
    return data


def read_image(path):
    with path.open("rb") as stream:
        payload = stream.read(MAX_BYTES + 1)
    if not 0 < len(payload) <= MAX_BYTES or not image_header(payload):
        raise ValueError("Invalid local image")
    return payload


def atomic_write(path, payload):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".part")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        with suppress(OSError):
            temporary.unlink()


class ImageStore:
    def __init__(self, config):
        self.config = config
        self.directory = config.longtu_local_dir.expanduser().resolve()
        self.index = read_index(Path(__file__).with_name("index.json"))
        self.local = {}
        self.verified = {}
        self.active = 0
        self.last_request = 0.0
        self.client = None
        self.task = None
        self.writable = True

    def _scan(self):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.writable = False
            logger.warning("龙图目录不可写，请配置 LONGTU_LOCAL_DIR；将使用可用图片或远程回退")
        try:
            for path in self.directory.iterdir():
                if path.name not in self.index or path.is_symlink() or not path.is_file():
                    continue
                if not 0 < path.stat().st_size <= MAX_BYTES:
                    continue
                with path.open("rb") as stream:
                    if image_header(stream.read(12)):
                        self.local[path.name] = path
        except OSError:
            logger.warning("龙图本地目录扫描失败")

    async def start(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True, timeout=self.config.longtu_timeout,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=2),
            headers={"User-Agent": "nonebot-plugin-longtu/0.2.0"},
        )
        if self.config.longtu_mode == "local":
            await offload(self._scan)
            if self.config.longtu_auto_download and self.writable:
                self.task = asyncio.create_task(self._worker())
        logger.info(f"龙图模式={self.config.longtu_mode}，本地图={len(self.local)}")

    async def close(self):
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        if self.client:
            await self.client.aclose()

    @asynccontextmanager
    async def foreground(self):
        self.active += 1
        self.last_request = time.monotonic()
        try:
            yield
        finally:
            self.active -= 1
            self.last_request = time.monotonic()

    async def _idle(self):
        while self.active or time.monotonic() - self.last_request < self.config.longtu_idle_seconds:
            await asyncio.sleep(1)

    async def _fetch(self, name):
        entry = self.index.get(name)
        if entry is None:
            raise ValueError("Image removed from index")
        data = bytearray()
        async with self.client.stream("GET", BASE_URL + name) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > entry["size"]:
                    raise ValueError("Image exceeds expected size")
        payload = bytes(data)
        digest = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if len(payload) != entry["size"] or digest != entry["sha"] or not image_header(payload):
            raise ValueError("Image integrity check failed")
        return payload

    async def _save(self, name, payload):
        if not self.writable:
            return
        path = self.directory / name
        try:
            await offload(atomic_write, path, payload)
        except OSError:
            self.writable = False
            logger.warning("龙图缓存写入失败，后台下载暂停；已有图片继续可用")
            return
        self.local[name] = path
        self.verified[name] = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()

    async def get_image(self, excluded=()):
        if self.config.longtu_mode == "local":
            choices = list(set(self.local) - set(excluded)) or list(self.local)
            random.shuffle(choices)
            for name in choices[:3]:
                try:
                    payload = await offload(read_image, self.local[name])
                    return name, payload
                except (OSError, ValueError):
                    self.local.pop(name, None)
                    self.verified.pop(name, None)
            if not self.config.longtu_remote_fallback:
                raise ValueError("No local images available")
        choices = list(set(self.index) - set(excluded)) or list(self.index)
        for name in random.sample(choices, min(3, len(choices))):
            try:
                payload = await self._fetch(name)
            except (httpx.HTTPError, ValueError):
                continue
            if self.config.longtu_mode == "local":
                await self._save(name, payload)
            return name, payload
        raise ValueError("No remote images available")

    async def _matches(self, name):
        entry = self.index[name]
        if self.verified.get(name) == entry["sha"] and name in self.local:
            return True
        path = self.local.get(name)
        if path is None:
            return False
        try:
            payload = await offload(read_image, path)
        except (OSError, ValueError):
            return False
        digest = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if digest == entry["sha"]:
            self.verified[name] = digest
            return True
        return False

    async def _worker(self):
        await asyncio.sleep(self.config.longtu_startup_delay)
        while self.writable:
            await self._idle()
            downloaded = 0
            failed = False
            for name in list(self.index):
                await self._idle()
                if not self.writable:
                    return
                if await self._matches(name):
                    continue
                try:
                    payload = await self._fetch(name)
                    await self._save(name, payload)
                    downloaded += 1
                except (httpx.HTTPError, OSError, ValueError) as exc:
                    logger.warning(f"龙图后台下载暂停后重试：{type(exc).__name__}")
                    failed = True
                    await asyncio.sleep(60)
                    continue
                await asyncio.sleep(self.config.longtu_download_interval)
            else:
                logger.info(f"龙图后台同步本轮结束，新增/更新={downloaded}，本地图={len(self.local)}，待重试={failed}")
                if not failed:
                    return
                await asyncio.sleep(60)
