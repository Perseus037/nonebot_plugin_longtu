import asyncio
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

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

    async def test_sparse_cache_does_not_limit_candidate_pool(self):
        names = [f"dragon_{i}_.gif" for i in range(4)]
        self.store.index = dict.fromkeys(names, ENTRY)
        await self.store._save(names[-1], IMAGE)
        candidates = []
        def ordered(items):
            candidates.extend(items)
            items.sort()
        with patch.object(storage.random, "shuffle", side_effect=ordered), patch.object(self.store, "_fetch", new=AsyncMock(return_value=IMAGE)) as fetch:
            self.assertEqual(await self.store.get_image(), (names[0], IMAGE))
        self.assertCountEqual(candidates, names)
        fetch.assert_awaited_once_with(names[0])
        self.assertEqual((self.path / names[0]).read_bytes(), IMAGE)

    async def test_selected_cached_image_does_not_use_network(self):
        self.store.index["dragon_2_.gif"] = ENTRY
        await self.store._save(NAME, IMAGE)
        with patch.object(storage.random, "shuffle", side_effect=lambda items: items.sort()), patch.object(self.store, "_fetch", new=AsyncMock()) as fetch:
            self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
        fetch.assert_not_awaited()

    async def test_selected_stale_image_downloads_same_name(self):
        other = "dragon_2_.gif"
        self.store.index[other] = ENTRY
        await self.store._save(other, IMAGE)
        for damage in ("deleted", "corrupt"):
            with self.subTest(damage=damage):
                await self.store._save(NAME, IMAGE)
                if damage == "deleted":
                    (self.path / NAME).unlink()
                else:
                    (self.path / NAME).write_bytes(b"broken image")
                with patch.object(storage.random, "shuffle", side_effect=lambda items: items.sort()), patch.object(self.store, "_fetch", new=AsyncMock(return_value=IMAGE)) as fetch:
                    self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
                fetch.assert_awaited_once_with(NAME)
                self.assertEqual((self.path / NAME).read_bytes(), IMAGE)

    async def test_failed_remote_candidate_can_fall_through_to_cached_image(self):
        other = "dragon_2_.gif"
        self.store.index[other] = ENTRY
        await self.store._save(other, IMAGE)
        with patch.object(storage.random, "shuffle", side_effect=lambda items: items.sort()), patch.object(self.store, "_fetch", new=AsyncMock(side_effect=httpx.ConnectError("offline"))) as fetch:
            self.assertEqual(await self.store.get_image(), (other, IMAGE))
        fetch.assert_awaited_once_with(NAME)

    async def test_offline_sparse_cache_excludes_uncached_index_entries(self):
        self.config.longtu_remote_fallback = False
        names = [f"dragon_{i}_.gif" for i in range(4)]
        self.store.index = dict.fromkeys(names, ENTRY)
        await self.store._save(names[-1], IMAGE)
        candidates = []
        with patch.object(storage.random, "shuffle", side_effect=lambda items: candidates.extend(items)), patch.object(self.store, "_fetch", new=AsyncMock()) as fetch:
            self.assertEqual(await self.store.get_image(), (names[-1], IMAGE))
        self.assertEqual(candidates, [names[-1]])
        fetch.assert_not_awaited()

    async def test_remote_mode_ignores_existing_local_cache(self):
        await self.store._save(NAME, IMAGE)
        self.config.longtu_mode = "remote"
        with patch.object(self.store, "_fetch", new=AsyncMock(return_value=IMAGE)) as fetch, patch.object(self.store, "_save", new=AsyncMock()) as save:
            self.assertEqual(await self.store.get_image(), (NAME, IMAGE))
        fetch.assert_awaited_once_with(NAME)
        save.assert_not_awaited()

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

    async def test_offline_tries_remaining_local_candidates(self):
        self.config.longtu_remote_fallback = False
        names = [f"dragon_{i}_.gif" for i in range(4)]
        self.store.index = dict.fromkeys(names, ENTRY)
        for name in names:
            await self.store._save(name, IMAGE)
        (self.path / names[0]).unlink()
        (self.path / names[1]).write_bytes(b"broken image")
        (self.path / names[2]).unlink()
        with patch.object(storage.random, "shuffle", side_effect=lambda items: items.sort()), patch.object(self.store, "_fetch", new=AsyncMock()) as fetch:
            self.assertEqual(await self.store.get_image(), (names[3], IMAGE))
        fetch.assert_not_awaited()
        self.assertEqual(set(self.store.local), {names[3]})
        self.assertEqual(set(self.store.verified), {names[3]})

    async def test_remote_tries_remaining_candidates(self):
        names = [f"dragon_{i}_.gif" for i in range(4)]
        self.store.index = dict.fromkeys(names, ENTRY)
        await self.store.client.aclose()
        def respond(request):
            name = request.url.path.rsplit("/", 1)[-1]
            self.calls.append(name)
            if name == names[0]:
                return httpx.Response(404)
            if name == names[1]:
                return httpx.Response(200, content=b"GIF89a" + b"1" * 30)
            if name == names[2]:
                raise httpx.ReadTimeout("timeout", request=request)
            return httpx.Response(200, content=IMAGE)
        self.store.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        for mode in ("remote", "local"):
            with self.subTest(mode=mode):
                self.config.longtu_mode = mode
                self.calls.clear()
                with patch.object(storage.random, "shuffle", side_effect=lambda items: items.sort()):
                    self.assertEqual(await self.store.get_image(), (names[3], IMAGE))
                self.assertEqual(self.calls, names)
                self.assertEqual((self.path / names[3]).exists(), mode == "local")

    async def test_remote_exhausts_candidates_once_without_repeating_excluded(self):
        self.config.longtu_mode = "remote"
        names = [f"dragon_{i}_.gif" for i in range(6)]
        self.store.index = dict.fromkeys(names, ENTRY)
        with patch.object(self.store, "_fetch", new=AsyncMock(side_effect=httpx.ConnectError("offline"))) as fetch:
            with self.assertRaisesRegex(ValueError, "No remote images available"):
                await self.store.get_image({names[0]})
        attempted = [call.args[0] for call in fetch.await_args_list]
        self.assertCountEqual(attempted, names[1:])

    async def test_candidates_respect_exclusions_and_allow_reuse_when_exhausted(self):
        names = [f"dragon_{i}_.gif" for i in range(5)]
        self.store.index = dict.fromkeys(names, ENTRY)
        for name in names:
            await self.store._save(name, IMAGE)
        for mode in ("local", "remote"):
            with self.subTest(mode=mode):
                self.config.longtu_mode = mode
                with patch.object(self.store, "_fetch", new=AsyncMock(return_value=IMAGE)):
                    selected, _ = await self.store.get_image(set(names[:-1]))
                    self.assertEqual(selected, names[-1])
                    selected, _ = await self.store.get_image(set(names))
                    self.assertIn(selected, names)

    async def test_offline_exhausts_and_removes_invalid_candidates(self):
        self.config.longtu_remote_fallback = False
        names = [f"dragon_{i}_.gif" for i in range(5)]
        self.store.local = {name: self.path / name for name in names}
        self.store.verified = dict.fromkeys(names, ENTRY["sha"])
        with patch.object(self.store, "_fetch", new=AsyncMock()) as fetch:
            with self.assertRaisesRegex(ValueError, "No local images available"):
                await self.store.get_image()
        self.assertEqual(self.store.local, {})
        self.assertEqual(self.store.verified, {})
        fetch.assert_not_awaited()

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

    async def test_worker_concurrency_and_completion(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.config.longtu_download_interval = 0
        self.store.index = {f"dragon_{i}_.gif": ENTRY for i in range(10)}
        active = peak = 0
        async def fetch(name):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(0.01)
                return IMAGE
            finally:
                active -= 1
        with patch.object(self.store, "_fetch", side_effect=fetch):
            await asyncio.wait_for(self.store._worker(), 3)
        self.assertEqual(peak, 3)
        self.assertEqual(len(self.store.local), 10)

    async def test_only_failed_images_retried(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.config.longtu_download_interval = 0
        names = [f"dragon_{i}_.gif" for i in range(6)]
        self.store.index = dict.fromkeys(names, ENTRY)
        attempts = dict.fromkeys(names, 0)
        async def download(name):
            attempts[name] += 1
            return name != names[0] or attempts[name] > 1
        sleeps = []
        real_sleep = asyncio.sleep
        async def fast_sleep(delay):
            sleeps.append(delay)
            await real_sleep(0)
        with patch.object(self.store, "_download", side_effect=download), patch.object(storage.asyncio, "sleep", side_effect=fast_sleep):
            await self.store._worker()
        self.assertEqual(attempts[names[0]], 2)
        self.assertTrue(all(attempts[n] == 1 for n in names[1:]))
        self.assertIn(5, sleeps)

    async def test_outage_exponential_backoff_is_capped(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.config.longtu_download_interval = 0
        sleeps = []
        real_sleep = asyncio.sleep
        async def fast_sleep(delay):
            sleeps.append(delay)
            await real_sleep(0)
        with patch.object(self.store, "_download", new=AsyncMock(side_effect=[False] * 6 + [True])), patch.object(storage.asyncio, "sleep", side_effect=fast_sleep):
            await self.store._worker()
        self.assertEqual([s for s in sleeps if s], [5, 10, 20, 40, 60, 60])

    async def test_foreground_stops_next_batch(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.config.longtu_download_interval = 0
        self.store.index = {f"dragon_{i}_.gif": ENTRY for i in range(6)}
        first_batch = asyncio.Event()
        release = asyncio.Event()
        calls = []
        async def fetch(name):
            calls.append(name)
            if len(calls) == 3:
                first_batch.set()
            await release.wait()
            return IMAGE
        with patch.object(self.store, "_fetch", side_effect=fetch):
            self.store.task = asyncio.create_task(self.store._worker())
            await asyncio.wait_for(first_batch.wait(), 1)
            async with self.store.foreground():
                release.set()
                await asyncio.sleep(0.05)
                self.assertEqual(len(calls), 3)
            await asyncio.wait_for(self.store.task, 2)
        self.assertEqual(len(calls), 6)

    async def test_shutdown_cancels_inflight_batch(self):
        self.config.longtu_startup_delay = 0
        self.config.longtu_idle_seconds = 0
        self.store.index = {f"dragon_{i}_.gif": ENTRY for i in range(6)}
        started = asyncio.Event()
        active = 0
        async def fetch(name):
            nonlocal active
            active += 1
            if active == 3:
                started.set()
            try:
                await asyncio.Event().wait()
            finally:
                active -= 1
        with patch.object(self.store, "_fetch", side_effect=fetch):
            self.store.task = asyncio.create_task(self.store._worker())
            await asyncio.wait_for(started.wait(), 1)
            await self.store.close()
        self.assertEqual(active, 0)


if __name__ == "__main__":
    unittest.main()
