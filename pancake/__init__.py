import sys
import os

disable_check = []

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

_initialized = False

def init():
    global _initialized
    if _initialized:
        return
    _initialized = True

    import initialize
    initialize.print_ico()

    init_rask = {"check_environment":initialize.check_environment, # 检查环境
                 "check_struct":initialize.check_struct, # 检查项目结构完整性
                }

    # 检查运行环境
    print("检查运行环境")
    import tool
    progress = tool.ProgressBar(len(init_rask), prefix="初始化环境")
    for task in init_rask.keys():
        if task in disable_check:
            continue
        init_rask[task]()
        progress.update(1, f"{task} 完成")

    progress.finish()

    # 初始化 dotenv 和 logging
    from resource import config  # noqa: F401
    import resource.logging as resource_logging  # noqa: F401


# 延迟导入，避免循环依赖
def run():
    init()
    from .run import run as _run
    _run()


# ---- 公开 API ----
from pancake.dough import Dough, Scope
from pancake.factory.dough_factory import DoughFactory
from pancake.registry import (
    register_class, get_class, get_all_classes,
    register_decorator, get_decorator, get_all_decorators,
)
from pancake.decorators import (
    DoughDecorator, Singleton, Prototype, Lazy,
    Maker, noMaker, inject, Config, DependsOn, Import,
)
from pancake.base import Configuration, Function, Service, Struct
