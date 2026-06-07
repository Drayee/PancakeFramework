"""
全局类注册表
无依赖，解决循环导入问题
"""

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


def clear_registry():
    """清空注册表（用于测试）"""
    _class_registry.clear()
