import random

from httpx import AsyncClient
from io import BytesIO

from nonebot import on_command
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.plugin import PluginMetadata

__version__ = "0.1.0.post1"
__plugin_meta__ = PluginMetadata(
    name = "随机龙图",
    description = "发送dragon，龙龙或者龙图随即发送一张可爱龙龙",
    usage = "使用命令：dragon，龙龙，龙图",
    type="application",
    homepage="https://github.com/Perseus037/nonebot_plugin_longtu",
    supported_adapters = {"nonebot.adapters.onebot.v11"},
)

dragon = on_command("dragon", aliases={"龙龙", "龙图"}, priority=5)

@dragon.handle()
async def handle_first_receive(bot: Bot, event: MessageEvent):
    base_url = "https://git.acwing.com/Est/dragon/-/raw/main/"
    extensions = ['.jpg', '.png', '.gif']

    batch_choice = random.choice(['batch1/', 'batch2/', 'batch3/'])

    if batch_choice == 'batch1/':
        selected_image_number = random.randint(1, 500)
        
    elif batch_choice == 'batch2/':
        selected_image_number = random.randint(501, 1000)
        
    else:
        selected_image_number = random.randint(1001, 1516)

    for ext in extensions:        
        image_url = f"{base_url}{batch_choice}dragon_{selected_image_number}_{ext}"
        try:
            async with AsyncClient() as client:
                resp = await client.get(image_url, timeout=5.0)
                
            if resp.status_code == 200:
                picbytes = BytesIO(resp.content).getvalue()
                await dragon.finish(MessageSegment.image(picbytes))
                break
                
        except Exception as e:
            if isinstance(e, FinishedException):
                pass
                
            else:
                print(f"尝试发送图片时出现异常：{e}")
              
                if ext == extensions[-1]:
                    await dragon.send("龙龙现在出不来了，稍后再试试吧~")
                  
