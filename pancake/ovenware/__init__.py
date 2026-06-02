from pancake import oven
import builtins
import logging

builtins.__dict__["oven"] = oven
builtins.__dict__["logging"] = logging

from abc import ABC, abstractmethod

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


class InitAction(ABC):

    name : str = "InitAction"

    init_order : int = 0
    build_order : int = 0

    _dependencies: list[str] = []
    _extras: str = None

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def build(self):
        pass

    @staticmethod
    def check():
        pass


class Decorator(ABC):

    @abstractmethod
    def build(self):
        pass

builtins.__dict__["InitAction"] = InitAction
builtins.__dict__["Decorator"] = Decorator
builtins.__dict__["check_dependencies"] = check_dependencies

