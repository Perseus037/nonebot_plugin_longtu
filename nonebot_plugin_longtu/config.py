from pydantic import BaseModel, Extra
from nonebot import get_driver

class Config(BaseModel, extra=Extra.ignore):
    max_dragons: int = 5  

config = get_driver().config
dragon_config: Config = Config.parse_obj(config.dict(exclude_unset=True))
max_dragons = dragon_config.max_dragons
