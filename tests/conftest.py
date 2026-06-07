"""共享 fixtures"""

import sys
import os
import pytest

# 确保 pancake 包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 添加插件包路径
plugin_dirs = [
    "pancake-mybatis",
    "pancake-redis",
    "pancake-ai",
    "pancake-cui",
    "pancake-gui",
    "pancake-remote",
    "pancake-langgraph",
    "pancake-embed",
    "pancake-web",
]
for plugin_dir in plugin_dirs:
    plugin_path = os.path.join(os.path.dirname(__file__), "..", plugin_dir)
    if os.path.isdir(plugin_path):
        sys.path.insert(0, plugin_path)


@pytest.fixture
def dough_factory():
    """独立的 DoughFactory 实例"""
    from pancake.factory.dough_factory import DoughFactory
    import uuid
    name = f"test_{uuid.uuid4().hex[:8]}"
    factory = DoughFactory(name)
    yield factory
    # 清理
    if name in DoughFactory._factories:
        del DoughFactory._factories[name]


@pytest.fixture
def clean_registry():
    """清空全局注册表（测试前后）"""
    from pancake.registry import clear_registry
    clear_registry()
    yield
    clear_registry()
