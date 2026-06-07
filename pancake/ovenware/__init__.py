"""
Ovenware 插件模块
提供插件基类和依赖检查工具
"""

import builtins
import logging

logger = logging.getLogger(__name__)


def check_dependencies(deps: list[str], extras: str = None) -> bool:
    """
    统一依赖检查

    Args:
        deps: 需要检查的 Python 包名列表
        extras: pip extras 名称（如 "redis", "ai"）

    Returns:
        True = 全部可用, False = 有缺失
    """
    missing = []
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    if not missing:
        return True
    msg = f"缺少可选依赖: {', '.join(missing)}"
    if extras:
        msg += f"，请运行: pip install pancake[{extras}]"
    logger.warning(msg)
    return False


# 注册到 builtins 供插件使用
builtins.__dict__["logging"] = logging
builtins.__dict__["check_dependencies"] = check_dependencies
