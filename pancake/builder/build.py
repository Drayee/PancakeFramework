"""构建模块 — 使用 DoughFactory 创建和启动所有 Bean"""

import logging
from pancake.factory.dough_factory import DoughFactory

logger = logging.getLogger(__name__)


def build():
    """创建所有 Bean 并启动"""
    factory = DoughFactory.get()
    factory.create_all()
    factory.startup_all()
