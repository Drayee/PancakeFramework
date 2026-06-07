"""工厂模块"""

from pancake.factory.dough_factory import DoughFactory

__all__ = ["DoughFactory"]


# 注册到 registry.water，供 embed 注入 builtins
from pancake.registry import water
water["DoughFactory"] = DoughFactory
