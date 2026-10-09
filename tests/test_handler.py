import asyncio
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
