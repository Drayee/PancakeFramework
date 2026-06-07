from pancake.base.configuration import Configuration
from pancake.base.function import Function
from pancake.base.service import Service
from pancake.base.struct import Struct

__all__ = ["Configuration", "Function", "Service", "Struct"]


# 注册基类到 registry.water，供 embed 注入 builtins
from pancake.registry import water
water["Configuration"] = Configuration
water["Function"] = Function
water["Service"] = Service
water["Struct"] = Struct
