"""CLI 工具函数"""

import os


def get_version():
    """获取框架版本"""
    try:
        from importlib.metadata import version
        return version("pancake_framework")
    except Exception:
        pass
    # 回退：从 pyproject.toml 读取
    try:
        import tomllib
        pyproject = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
        with open(pyproject, "rb") as f:
            return tomllib.load(f)["tool"]["poetry"]["version"]
    except Exception:
        pass
    return "unknown"
