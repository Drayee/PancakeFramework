"""工厂模块"""

from pancake.factory.dough_factory import DoughFactory

__all__ = ["DoughFactory"]


# 注册到 muffin_water，供 DoughMeta 零 import 注入
def _register_to_muffin():
    from pancake.oven.muffin import muffin_water
    muffin_water["DoughFactory"] = DoughFactory

_register_to_muffin()
