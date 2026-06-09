"""Struct 基类"""

from dataclasses import dataclass
from pancake.dough import Dough


@dataclass
class Struct(Dough):
    _no_register = True
    """数据结构类 — 同时继承 Dough 和 dataclass

    支持两种注入模式:
    1. @config 标记的字段从配置注入
    2. 构造函数传入
    """
    pass
