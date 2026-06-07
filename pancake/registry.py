"""
统一注册表
管理框架所有注册数据：类、装饰器、实例、运行时数据
"""

import warnings
from collections import defaultdict


# ============================================================
#  类注册表（DoughMeta 自动注册）
# ============================================================

_class_registry: dict[str, type] = {}


def register_class(name: str, cls: type):
    """注册类到全局注册表"""
    _class_registry[name] = cls


def get_class(name: str) -> type | None:
    """从注册表获取类"""
    return _class_registry.get(name)


def get_all_classes() -> dict[str, type]:
    """获取所有注册的类（返回副本）"""
    return dict(_class_registry)


# ============================================================
#  装饰器注册表
# ============================================================

_decorator_registry: dict[str, object] = {}


def register_decorator(name: str, decorator: object):
    """注册装饰器到全局注册表"""
    _decorator_registry[name] = decorator


def get_decorator(name: str) -> object | None:
    """从注册表获取装饰器"""
    return _decorator_registry.get(name)


def get_all_decorators() -> dict[str, object]:
    """获取所有注册的装饰器（返回副本）"""
    return dict(_decorator_registry)


def has_decorator(name: str) -> bool:
    """检查装饰器是否已注册"""
    return name in _decorator_registry


# ============================================================
#  实例注册表
# ============================================================

_instance_registry: dict[str, object] = {}


def register_instance(name: str, instance: object):
    """注册实例"""
    _instance_registry[name] = instance


def get_instance(name: str) -> object | None:
    """获取实例"""
    return _instance_registry.get(name)


def get_all_instances() -> dict[str, object]:
    """获取所有注册的实例（返回副本）"""
    return dict(_instance_registry)


# ============================================================
#  运行时数据注册表
# ============================================================

_runtime_registry: dict[str, object] = {}


def set_runtime(key: str, value: object):
    """设置运行时数据"""
    _runtime_registry[key] = value


def get_runtime(key: str, default=None) -> object:
    """获取运行时数据"""
    return _runtime_registry.get(key, default)


# ============================================================
#  装饰器/类 API（原 muffin_flour / muffin_water）
#  供 embed 插件注入 builtins
# ============================================================

# 装饰器 API：{名称: 装饰器函数}
flour: dict[str, object] = {}

# 类 API：{名称: 类对象}
water: dict[str, object] = {}

# 方法/构建器 API
egg: dict[str, object] = {}

# 其他 API
sugar: dict[str, object] = {}


# 向后兼容别名（muffin 模块迁移）
muffin_flour = flour
muffin_water = water
muffin_egg = egg
muffin_sugar = sugar


# ============================================================
#  清理
# ============================================================

def clear_registry():
    """清空所有注册表（用于测试）

    注意：flour/water/egg/sugar 不清空，它们是框架内置 API。
    """
    _class_registry.clear()
    _decorator_registry.clear()
    _instance_registry.clear()
    _runtime_registry.clear()
    # flour/water/egg/sugar 保留，它们是静态框架 API


# ============================================================
#  注册 registry 自身的函数到 water（供 embed 注入）
# ============================================================

water["register_class"] = register_class
water["get_class"] = get_class
water["get_all_classes"] = get_all_classes
water["register_decorator"] = register_decorator
water["get_decorator"] = get_decorator
water["get_all_decorators"] = get_all_decorators
