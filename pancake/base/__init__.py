from pancake.base.configuration import Configuration
from pancake.base.function import Function
from pancake.base.service import Service
from pancake.base.struct import Struct

__all__ = ["Configuration", "Function", "Service", "Struct"]


# 注册基类到 muffin_water，供 DoughMeta 零 import 注入
def _register_to_muffin():
    from pancake.oven.muffin import muffin_water
    muffin_water["Configuration"] = Configuration
    muffin_water["Function"] = Function
    muffin_water["Service"] = Service
    muffin_water["Struct"] = Struct

_register_to_muffin()
