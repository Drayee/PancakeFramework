"""
IoC 容器 - 控制反转和依赖注入
支持构造函数注入、属性注入、作用域管理
"""

import functools
import inspect
import logging
from enum import Enum
from typing import Any, Callable, Type, get_type_hints

logger = logging.getLogger(__name__)


class Scope(Enum):
    """依赖作用域"""
    SINGLETON = "singleton"    # 单例 - 全局唯一
    TRANSIENT = "transient"    # 瞬态 - 每次创建新实例
    SCOPED = "scoped"          # 作用域 - 同一流程内单例


class IoCContainer:
    """IoC 容器 - 管理依赖注册和解析"""

    def __init__(self):
        self._registrations: dict[str, dict] = {}
        self._singletons: dict[str, Any] = {}
        self._scoped: dict[str, Any] = {}

    def register(self, interface: Type = None, implementation: Any = None,
                 scope: Scope = Scope.TRANSIENT, factory: Callable = None):
        """
        注册依赖

        Args:
            interface: 接口类型（或类名）
            implementation: 实现类或实例
            scope: 作用域
            factory: 工厂函数
        """
        key = interface.__name__ if interface else implementation.__name__

        self._registrations[key] = {
            "interface": interface,
            "implementation": implementation,
            "scope": scope,
            "factory": factory,
        }

        # 如果是单例且已提供实例，直接存储
        if scope == Scope.SINGLETON and implementation and not inspect.isclass(implementation):
            self._singletons[key] = implementation

        logger.info(f"IoC 注册: {key} ({scope.value})")

    def register_singleton(self, interface: Type, implementation: Any = None):
        """注册单例"""
        self.register(interface, implementation, Scope.SINGLETON)

    def register_transient(self, interface: Type, implementation: Any = None):
        """注册瞬态"""
        self.register(interface, implementation, Scope.TRANSIENT)

    def register_scoped(self, interface: Type, implementation: Any = None):
        """注册作用域"""
        self.register(interface, implementation, Scope.SCOPED)

    def resolve(self, interface: Type) -> Any:
        """
        解析依赖

        Args:
            interface: 接口类型

        Returns:
            解析后的实例
        """
        key = interface.__name__ if inspect.isclass(interface) else interface

        if key not in self._registrations:
            raise ValueError(f"未注册的依赖: {key}")

        reg = self._registrations[key]
        scope = reg["scope"]

        # 单例
        if scope == Scope.SINGLETON:
            if key in self._singletons:
                return self._singletons[key]
            instance = self._create_instance(reg)
            self._singletons[key] = instance
            return instance

        # 作用域
        if scope == Scope.SCOPED:
            if key in self._scoped:
                return self._scoped[key]
            instance = self._create_instance(reg)
            self._scoped[key] = instance
            return instance

        # 瞬态
        return self._create_instance(reg)

    def _create_instance(self, reg: dict) -> Any:
        """创建实例"""
        # 使用工厂函数
        if reg["factory"]:
            return reg["factory"]()

        impl = reg["implementation"]

        # 如果是实例，直接返回
        if not inspect.isclass(impl):
            return impl

        # 获取构造函数参数
        sig = inspect.signature(impl.__init__)
        hints = get_type_hints(impl.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # 尝试从容器解析
            param_type = hints.get(param_name)
            if param_type and param_type.__name__ in self._registrations:
                kwargs[param_name] = self.resolve(param_type)
            elif param.default is not inspect.Parameter.empty:
                kwargs[param_name] = param.default

        return impl(**kwargs)

    def inject(self, func: Callable = None, **named_deps):
        """
        自动注入装饰器

        Args:
            func: 要注入的函数
            **named_deps: 命名依赖映射
        """
        def decorator(f):
            hints = get_type_hints(f)
            sig = inspect.signature(f)

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # 注入缺失的参数
                for param_name, param in sig.parameters.items():
                    if param_name in kwargs:
                        continue

                    param_type = hints.get(param_name)
                    if param_type:
                        # 检查命名映射
                        if param_name in named_deps:
                            kwargs[param_name] = named_deps[param_name]
                        # 从容器解析
                        elif param_type.__name__ in self._registrations:
                            kwargs[param_name] = self.resolve(param_type)

                return f(*args, **kwargs)

            return wrapper

        if func:
            return decorator(func)
        return decorator

    def clear_scoped(self):
        """清除作用域实例"""
        self._scoped.clear()

    def clear_all(self):
        """清除所有"""
        self._registrations.clear()
        self._singletons.clear()
        self._scoped.clear()


# 全局容器
container = IoCContainer()


def inject(func: Callable = None, **named_deps):
    """全局注入装饰器快捷方式"""
    return container.inject(func, **named_deps)


# 注册到 muffin_water/muffin_flour，使其被 embed 自动注入到 builtins
oven.muffin_water["IoCContainer"] = IoCContainer
oven.muffin_water["Scope"] = Scope
oven.muffin_flour["inject"] = inject
oven.muffin_suger["container"] = container
