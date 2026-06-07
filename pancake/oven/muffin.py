"""
Muffin 注册表 — 向后兼容
实际数据已迁移到 registry.py
"""

import warnings

from pancake.registry import (
    flour as muffin_flour,
    water as muffin_water,
    egg as muffin_egg,
    sugar as muffin_sugar,
)


class _DeprecatedAlias:
    """延迟 deprecation warning 的代理对象"""
    def __init__(self, target, old_name, new_name):
        object.__setattr__(self, '_target', target)
        object.__setattr__(self, '_old_name', old_name)
        object.__setattr__(self, '_new_name', new_name)

    def _warn(self):
        warnings.warn(
            f"{self._old_name} 已弃用，请使用 registry.{self._new_name}",
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


# 旧拼写兼容
muffin_suger = _DeprecatedAlias(muffin_sugar, "muffin_suger", "muffin_sugar")


def create_registry():
    """向后兼容 — 已弃用"""
    warnings.warn("create_registry() 已弃用，使用 registry.clear_registry()", DeprecationWarning)
    return None
