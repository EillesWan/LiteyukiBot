from nonebot.plugin import PluginMetadata

from liteyuki import get_bot
from .crt_matchers import *  # type: ignore
from .rt_guide import *  # type: ignore

__plugin_meta__ = PluginMetadata(

    name="CRT生成工具",
    description="一些CRT牌子生成器",
    usage="我觉得你应该会用",
    type="application",
    homepage="https://github.com/snowykami/LiteyukiBot",
    extra={
            "liteyuki"      : True,
            "toggleable"    : True,
            "default_enable": True,
    }
)