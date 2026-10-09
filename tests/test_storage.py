import asyncio
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

ROOT = Path(__file__).resolve().parents[1] / "nonebot_plugin_longtu"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


storage = load("storage")
Config = load("config").Config
IMAGE = b"GIF89a" + b"\x00" * 30
NAME = "dragon_1_.gif"
ENTRY = {"size": len(IMAGE), "sha": hashlib.sha1(f"blob {len(IMAGE)}\0".encode() + IMAGE).hexdigest()}


class StorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "images"
        self.config = Config(longtu_local_dir=self.path, longtu_auto_download=False)
        self.store = storage.ImageStore(self.config)
        await self.store.start()
        self.store.index = {NAME: ENTRY}
        self.calls = []

    async def asyncTearDown(self):
        await self.store.close()
        self.tmp.cleanup()

    async def transport(self, content=IMAGE, status=200):
        await self.store.client.aclose()
        def respond(request):
            self.calls.append(str(request.url))
            return httpx.Response(status, content=content)
        self.store.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))

    async def test_remote_download_then_offline_cache(self):
        await self.transport()
        self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
        self.assertEqual((self.path / NAME).read_bytes(), IMAGE)
        await self.transport(status=503)
        self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
        self.assertEqual(len(self.calls), 1)

    async def test_remote_mode_never_writes(self):
        self.config.longtu_mode = "remote"
        await self.transport()
        await self.store.get_image()
        self.assertFalse((self.path / NAME).exists())
        self.assertEqual(self.store.local, {})

    async def test_remote_start_does_not_create_directory_or_worker(self):
        cfg = Config(longtu_mode="remote", longtu_local_dir=self.path / "absent")
        other = storage.ImageStore(cfg)
        await other.start()
        self.assertFalse(other.directory.exists())
        self.assertIsNone(other.task)
        await other.close()

    async def test_offline_empty_does_not_call_network(self):
        self.config.longtu_remote_fallback = False
        await self.transport()
        with self.assertRaises(ValueError):
            await self.store.get_image()
        self.assertEqual(self.calls, [])

    async def test_corrupt_download_not_cached(self):
        await self.transport(content=b"<html>error</html>")
        with self.assertRaises(ValueError):
            await self.store.get_image()
        self.assertEqual(list(self.path.iterdir()), [])

    async def test_wrong_hash_not_cached(self):
        await self.transport(content=b"GIF89a" + b"1" * 30)
        with self.assertRaises(ValueError):
            await self.store.get_image()
        self.assertEqual(self.store.local, {})

    async def test_http_failure_bounded(self):
        await self.transport(status=503)
        with self.assertRaises(ValueError):
            await self.store.get_image()
        self.assertEqual(len(self.calls), 1)

    async def test_resume_scans_existing_and_ignores_partial(self):
        (self.path / NAME).write_bytes(IMAGE)
        (self.path / "unfinished.gif.part").write_bytes(IMAGE)
        (self.path / "broken.jpg").write_bytes(b"not an image")
        await storage.offload(self.store._scan)
        self.assertEqual(list(self.store.local), [NAME])
        self.assertTrue(await self.store._matches(NAME))
        self.store.index[NAME] = dict(ENTRY, sha="0" * 40)
        self.assertFalse(await self.store._matches(NAME))

    async def test_readonly_cache_still_sends_download(self):
        await self.transport()
        with patch.object(storage, "atomic_write", side_effect=PermissionError):
            self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
        self.assertFalse(self.store.writable)

    async def test_atomic_failure_preserves_existing(self):
        path = self.path / NAME
        path.write_bytes(IMAGE)
        with patch.object(Path, "replace", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                storage.atomic_write(path, b"new")
        self.assertEqual(path.read_bytes(), IMAGE)
        self.assertEqual(list(self.path.iterdir()), [path])

    async def test_foreground_pauses_worker(self):
        self.config.longtu_idle_seconds = 0
        async with self.store.foreground():
            waiter = asyncio.create_task(self.store._idle())
            await asyncio.sleep(0.01)
            self.assertFalse(waiter.done())
        await asyncio.wait_for(waiter, 1.5)
        self.assertEqual(self.store.active, 0)

    async def test_shutdown_cancels_background(self):
        self.store.task = asyncio.create_task(asyncio.sleep(100))
        await self.store.close()
        self.assertTrue(self.store.task.cancelled())

    async def test_index_rejects_unsafe_paths(self):
        path = self.path / "index.json"
        path.write_text(json.dumps({"../../bad.gif": ENTRY}))
        with self.assertRaises(ValueError):
            storage.read_index(path)

    async def test_unknown_local_images_not_selected(self):
        (self.path / "unknown.gif").write_bytes(IMAGE)
        await storage.offload(self.store._scan)
        self.assertEqual(self.store.local, {})

    async def test_multiple_images_no_repeat(self):
        self.store.index["dragon_2_.gif"] = ENTRY
        for name in [NAME, "dragon_2_.gif"]:
            (self.path / name).write_bytes(IMAGE)
        await storage.offload(self.store._scan)
        first, _ = await self.store.get_image()
        second, _ = await self.store.get_image({first})
        self.assertNotEqual(first, second)

    async def test_worker_downloads_and_restart_skips(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.config.longtu_download_interval = 0.01
        await self.store.client.aclose()
        def respond(request):
            self.calls.append(str(request.url))
            return httpx.Response(200, content=IMAGE)
        self.store.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        self.store.task = asyncio.create_task(self.store._worker())
        for _ in range(100):
            if NAME in self.store.local:
                break
            await asyncio.sleep(0.01)
        self.assertIn(NAME, self.store.local)
        await asyncio.wait_for(self.store.task, 1)
        self.assertEqual(self.calls, [storage.BASE_URL + NAME])
        await self.store.close()
        other = storage.ImageStore(self.config)
        other.index = {NAME: ENTRY}
        await other.start()
        self.assertTrue(await other._matches(NAME))
        await other.close()


if __name__ == "__main__":
    unittest.main()
