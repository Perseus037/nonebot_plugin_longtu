import os
import re
import random
from io import BytesIO

from httpx import AsyncClient, ReadTimeout, ConnectError

from nonebot import on_command
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

try:
    from .config import max_dragons as CFG_MAX_DRAGONS
except Exception:
    CFG_MAX_DRAGONS = None

__version__ = "0.1.2"
__plugin_meta__ = PluginMetadata(
    name="随机龙图",
    description="2024年是龙年...我都准备好了",
    usage="使用命令：龙龙，龙图，dragon（可加数量，如“龙图 3”）",
    homepage="https://github.com/Perseus037/nonebot_plugin_longtu",
    type="application",
    config=None,
    supported_adapters={"~onebot.v11"},
)

dragon = on_command("dragon", aliases={"龙龙", "龙图"}, priority=5, block=True)


@dragon.handle()
async def handle_first_receive(bot: Bot, event: MessageEvent):
    base_url = "https://raw.githubusercontent.com/Whiked/Dragonimg/main/drimg/"
    extensions = [".jpg", ".png", ".gif"]
    total_images = 1516

    text = event.message.extract_plain_text().strip()
    m = re.search(r"\b(\d{1,2})\b", text)
    try:
        req_n = int(m.group(1)) if m else 1
    except Exception:
        req_n = 1

    limit = CFG_MAX_DRAGONS if isinstance(CFG_MAX_DRAGONS, int) else int(os.getenv("MAX_DRAGONS", "5"))
    n = max(1, min(req_n, limit))

    sent = 0
    tried = 0
    while sent < n and tried < n * 4:
        selected_image_number = random.randint(1, total_images)
        got_one = False

        for ext in extensions:
            image_url = f"{base_url}dragon_{selected_image_number}_{ext}"
            try:
                async with AsyncClient(follow_redirects=True) as client:
                    resp = await client.get(image_url, timeout=8.0)

                if resp.status_code == 200 and resp.content:
                    picbytes = BytesIO(resp.content).getvalue()
                    if sent < n - 1:
                        await dragon.send(MessageSegment.image(picbytes))
                    else:
                        await dragon.finish(MessageSegment.image(picbytes))
                    sent += 1
                    got_one = True
                    break

            except FinishedException:
                raise
            except ConnectError:
                logger.error(f"连接错误：无法访问 {image_url}")
                continue
            except ReadTimeout:
                logger.error(f"读取超时：{image_url}")
                continue
            except Exception as e:
                logger.error(f"输出异常：{e}")
                continue

        tried += 1
        if not got_one:
            continue

    if sent == 0:
        await dragon.send("龙龙现在出不来了，稍后再试试吧~")
