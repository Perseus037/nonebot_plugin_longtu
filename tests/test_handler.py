import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import nonebot
from nonebot.adapters.onebot.v11 import Adapter, Message

nonebot.init()
nonebot.get_driver().register_adapter(Adapter)
plugin = nonebot.load_plugin("nonebot_plugin_longtu").module


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        @asynccontextmanager
        async def foreground():
            yield
        self.store = SimpleNamespace(
            foreground=foreground,
            get_image=AsyncMock(return_value=("image.gif", b"GIF89a")),
        )
        self.sender = SimpleNamespace(send=AsyncMock())

    async def run_command(self, text):
        event = SimpleNamespace(message=Message(text))
        with patch.object(plugin, "store", self.store), patch.object(plugin, "dragon", self.sender):
            await plugin.handle_first_receive(event)

    async def test_single_and_multiple(self):
        await self.run_command("龙图 3")
        self.assertEqual(self.sender.send.await_count, 3)
        self.assertTrue(all(c.args[0].type == "image" for c in self.sender.send.await_args_list))

    async def test_large_count_clamped(self):
        await self.run_command("dragon 99999999999999999999999")
        self.assertEqual(self.sender.send.await_count, plugin.config.max_dragons)

    async def test_empty_cache_feedback_once(self):
        self.store.get_image.side_effect = ValueError("empty")
        await self.run_command("龙图 3")
        self.assertEqual(self.sender.send.await_count, 1)
        self.assertIsInstance(self.sender.send.call_args.args[0], str)

    async def test_no_repeated_send_on_protocol_error(self):
        self.sender.send.side_effect = RuntimeError("protocol failed")
        with self.assertRaises(RuntimeError):
            await self.run_command("龙图 3")
        self.assertEqual(self.store.get_image.await_count, 1)
        self.assertEqual(self.sender.send.await_count, 1)

    async def test_request_timeout(self):
        async def slow(_):
            await asyncio.sleep(10)
        self.store.get_image.side_effect = slow
        with patch.object(plugin.config, "longtu_request_timeout", 0.01):
            await self.run_command("龙图")
        self.assertEqual(self.sender.send.await_count, 1)

    async def test_partial_success_no_extra_feedback(self):
        self.store.get_image.side_effect = [("image.gif", b"GIF89a"), ValueError("offline")]
        await self.run_command("龙图 3")
        self.assertEqual(self.sender.send.await_count, 1)
        self.assertEqual(self.sender.send.call_args.args[0].type, "image")

    async def test_multiple_images_share_remaining_timeout_and_exclusions(self):
        budgets = []
        exclusions = []
        async def get_image(excluded):
            exclusions.append(set(excluded))
            return f"image_{len(exclusions)}.gif", b"GIF89a"
        async def wait_for(awaitable, timeout):
            budgets.append(timeout)
            return await awaitable
        self.store.get_image.side_effect = get_image
        with patch.object(plugin.config, "longtu_request_timeout", 20), patch.object(plugin, "time", SimpleNamespace(monotonic=lambda: next(ticks))), patch.object(plugin.asyncio, "wait_for", side_effect=wait_for):
            ticks = iter([0, 3, 10, 14, 20, 22])
            await self.run_command("龙图 3")
        self.assertEqual(budgets, [20, 17, 13])
        self.assertEqual(exclusions, [set(), {"image_1.gif"}, {"image_1.gif", "image_2.gif"}])

    async def test_candidate_fallback_still_cancelled_by_request_timeout(self):
        for mode in ("local", "remote"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                cfg = plugin.Config(longtu_mode=mode, longtu_local_dir=Path(directory), longtu_auto_download=False)
                self.store = plugin.ImageStore(cfg)
                names = [f"dragon_{i}_.gif" for i in range(6)]
                self.store.index = dict.fromkeys(names, {})
                calls = []
                cancelled = asyncio.Event()
                async def fetch(name):
                    calls.append(name)
                    if len(calls) <= 3:
                        raise httpx.ConnectError("offline")
                    try:
                        await asyncio.Event().wait()
                    finally:
                        cancelled.set()
                self.sender.send.reset_mock()
                with patch.object(self.store, "_fetch", side_effect=fetch), patch.object(plugin.config, "longtu_request_timeout", 0.05):
                    await asyncio.wait_for(self.run_command("龙图 3"), 2)
                self.assertEqual(len(calls), 4)
                self.assertTrue(cancelled.is_set())
                self.assertEqual(self.store.active, 0)
                self.assertEqual(self.sender.send.await_count, 1)
                self.assertIsInstance(self.sender.send.call_args.args[0], str)
