import asyncio
import re
import time

from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config
from .storage import ImageStore

__version__ = "0.2.1"
__plugin_meta__ = PluginMetadata(
    name="随机龙图",
    description="随机发送龙图，支持远程图片和本地渐进缓存",
    usage="龙龙、龙图、dragon（可加数量，如“龙图 3”）",
    homepage="https://github.com/Perseus037/nonebot_plugin_longtu",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

config = Config(**get_driver().config.dict())
store = ImageStore(config)
get_driver().on_startup(store.start)
get_driver().on_shutdown(store.close)
dragon = on_command("dragon", aliases={"龙龙", "龙图"}, priority=5, block=True)


@dragon.handle()
async def handle_first_receive(event: MessageEvent):
    match = re.search(r"\b(\d+)\b", event.message.extract_plain_text())
    count = min(int(match.group(1)[:6]), config.max_dragons) if match else 1
    count = max(1, count)
    sent = 0
    used = set()
    remaining = config.longtu_request_timeout
    async with store.foreground():
        for _ in range(count):
            started = time.monotonic()
            try:
                name, payload = await asyncio.wait_for(store.get_image(used), remaining)
            except (OSError, ValueError, asyncio.TimeoutError) as exc:
                logger.warning(f"龙图资源读取失败：{type(exc).__name__}")
                break
            remaining -= time.monotonic() - started
            used.add(name)
            await dragon.send(MessageSegment.image(payload))
            sent += 1
            if remaining <= 0:
                break
    if sent == 0:
        await dragon.send("龙龙现在出不来了，稍后再试试吧~")
