import logging
import signal
import sys

from pancake import oven
from .tool import ProgressBar
from . import builder
from pancake.oven import default

logger = logging.getLogger("Pancake_Main")

def load_xml():
    """加载 XML 启动配置"""
    from pancake.resource import xml_config
    xml_data = xml_config.load_xml()
    oven.pancake_xml.update(xml_data)

def load_config():
    """加载配置文件"""
    default.default_before()

def load_ovenware():
    """加载功能"""
    builder.load_dlc.run()

def oven_init():
    """初始化oven"""
    default.default_after()

def load_dish():
    """加载用户代码"""
    builder.load_src.run()

def run_loop_methods():
    """运行所有 loop_method"""
    for name, method in oven.muffin_egg.get("LoopMethod", {}).items():
        logger.info(f"运行 loop_method: {name}")
        method()

def build_all():
    """构建服务"""
    builder.build.build()

def _shutdown_handler(signum, frame):
    """信号处理：优雅关闭"""
    sig_name = signal.Signals(signum).name
    logger.info(f"收到信号 {sig_name}，正在优雅关闭...")

    # 关闭 lifecycle 管理的所有实例
    from pancake.ovenware.lifecycle import lifecycle_manager
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(lifecycle_manager.shutdown_all())
    except RuntimeError:
        asyncio.run(lifecycle_manager.shutdown_all())

    logger.info("Pancake 已关闭")
    sys.exit(0)


def run():
    """运行服务"""
    # 注册信号处理
    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)

    loading_list = {
        "load xml": load_xml,
        "load config": load_config,
        "load ovenware": load_ovenware,
        "oven init": oven_init,
        "load dish": load_dish,
        "build": build_all,
    }

    logger.info("Pancake Loading...")

    progress_bar = ProgressBar(len(loading_list), "Pancake Loading")

    for task in loading_list.keys():
        loading_list[task]()
        progress_bar.update(1, f"{task} 完成")
    progress_bar.finish()
    logger.info("Pancake Loading 完成")

    logger.info("Pancake 启动完成")

    # 运行 loop_method（如 web 服务器）
    run_loop_methods()
