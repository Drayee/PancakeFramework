"""
Muffin 注册表
管理框架自带的装饰器、类、方法
"""

import warnings


class MuffinRegistry:
    """
    Muffin 注册表 — 封装框架插件状态

    属性:
        flour: 装饰器 {"Mapper": ..., "get_controller": ...}
        water: 类 {"IoCContainer": ..., "Lifecycle": ...}
        egg:   方法/构建器 {"Builder": {}, "LoopMethod": {}}
        sugar: 其他 {"container": ...}
    """

    def __init__(self):
        self.flour: dict = {}
        self.water: dict = {}
        self.egg: dict = {}
        self.sugar: dict = {}

    def reset(self):
        """重置所有状态（用于测试）"""
        for d in (self.flour, self.water, self.egg, self.sugar):
            d.clear()


# 向后兼容的模块级默认实例
_registry = MuffinRegistry()

muffin_flour = _registry.flour
muffin_water = _registry.water
muffin_egg = _registry.egg
muffin_sugar = _registry.sugar


class _DeprecatedAlias:
    """延迟 deprecation warning 的代理对象"""
    def __init__(self, target, old_name, new_name):
        object.__setattr__(self, '_target', target)
        object.__setattr__(self, '_old_name', old_name)
        object.__setattr__(self, '_new_name', new_name)

    def _warn(self):
        warnings.warn(
            f"{self._old_name} 已弃用，请使用 {self._new_name}",
            DeprecationWarning,
            stacklevel=2,
        )

    def __getitem__(self, key):
        self._warn()
        return self._target[key]

    def __setitem__(self, key, value):
        self._warn()
        self._target[key] = value

    def __contains__(self, key):
        self._warn()
        return key in self._target

    def __iter__(self):
        self._warn()
        return iter(self._target)

    def __len__(self):
        self._warn()
        return len(self._target)

    def items(self):
        self._warn()
        return self._target.items()

    def keys(self):
        self._warn()
        return self._target.keys()

    def values(self):
        self._warn()
        return self._target.values()

    def get(self, key, default=None):
        self._warn()
        return self._target.get(key, default)

    def clear(self):
        self._warn()
        return self._target.clear()


muffin_suger = _DeprecatedAlias(_registry.sugar, "muffin_suger", "muffin_sugar")


def create_registry() -> MuffinRegistry:
    """创建新的独立注册表（用于测试）"""
    return MuffinRegistry()
