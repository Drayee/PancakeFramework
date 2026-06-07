"""
DoughFactory — Bean 工厂
直接读取 registry._class_registry，不维护独立的 _classes
"""

import asyncio
import inspect
import logging
from pancake.dough import Dough, Scope, _call_lifecycle
from pancake.registry import get_class, get_all_classes, register_instance, get_instance, get_all_instances

logger = logging.getLogger(__name__)


class DoughFactory:
    """Bean 工厂 — 管理 Bean 的创建、生命周期

    类注册表统一在 registry._class_registry，
    DoughFactory 直接读取，不维护独立副本。
    """

    _factories: dict[str, "DoughFactory"] = {}

    def __init__(self, name: str = "default"):
        self.name = name
        self._load_order: list[str] = []
        # 实例存储在 registry，这里只保留引用
        DoughFactory._factories[name] = self

    @staticmethod
    def get(name: str = "default") -> "DoughFactory":
        """获取或创建工厂实例"""
        if name not in DoughFactory._factories:
            DoughFactory._factories[name] = DoughFactory(name)
        return DoughFactory._factories[name]

    def register(self, cls: type):
        """注册 Bean 类（写入 registry）"""
        from pancake.registry import register_class
        name = cls.__name__
        register_class(name, cls)
        logger.debug(f"注册 Bean: {name}")

    def register_instance(self, name: str, instance: object):
        """注册已创建的实例"""
        register_instance(name, instance)
        logger.debug(f"注册实例: {name}")

    def resolve(self, name: str) -> Dough:
        """获取 Bean 实例"""
        # 已有实例
        instance = get_instance(name)
        if instance is not None:
            # Prototype 每次返回新实例
            if hasattr(instance, '_scope') and instance._scope == Scope.PROTOTYPE:
                cls = get_class(name)
                if cls:
                    return cls()
            return instance

        # Lazy 创建
        cls = get_class(name)
        if cls is None:
            raise ValueError(f"未注册的 Bean: {name}")

        if cls._scope == Scope.LAZY:
            instance = cls()
            register_instance(name, instance)
            return instance

        raise ValueError(f"Bean {name} 尚未创建，请先调用 create_all()")

    def _resolve_dependency_order(self) -> list[str]:
        """拓扑排序确定 Bean 创建顺序（依赖优先）

        使用 Kahn 算法：先计算入度，再依次取出入度为 0 的节点。
        LAZY Bean 不参与排序（延迟创建）。
        """
        all_classes = get_all_classes()

        deps: dict[str, list[str]] = {}
        for name, cls in all_classes.items():
            if cls._scope == Scope.LAZY:
                continue
            deps[name] = getattr(cls, '_depends_on', [])

        in_degree: dict[str, int] = {name: 0 for name in deps}
        for name, dep_list in deps.items():
            for dep in dep_list:
                if dep in in_degree:
                    in_degree[name] += 1

        queue = [name for name, degree in in_degree.items() if degree == 0]
        order: list[str] = []

        while queue:
            queue.sort()
            node = queue.pop(0)
            order.append(node)

            for name, dep_list in deps.items():
                if node in dep_list:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        if len(order) != len(deps):
            remaining = [n for n in deps if n not in order]
            raise ValueError(f"检测到循环依赖: {remaining}")

        return order

    # ---- 同步 API（兼容） ----

    def create_all(self):
        """创建所有注册的 Bean（同步版本，仅适用于纯同步生命周期）

        如果生命周期方法是 async 的，请使用 async_create_all()。
        """
        all_classes = get_all_classes()

        for name, cls in list(all_classes.items()):
            imports = getattr(cls, '_imports', [])
            for imported_cls in imports:
                if imported_cls.__name__ not in get_all_classes():
                    self.register(imported_cls)

        order = self._resolve_dependency_order()

        for name in order:
            cls = get_class(name)
            try:
                instance = cls()
                register_instance(name, instance)
                self._load_order.append(name)
                # 同步调用 on_init（仅当方法不是 async 时）
                method = getattr(instance, 'on_init', None)
                if method and not inspect.iscoroutinefunction(method):
                    method()
                logger.debug(f"创建 Bean: {name}")
            except Exception as e:
                logger.error(f"创建 Bean {name} 失败: {e}")
                raise

    def startup_all(self):
        """执行所有 Bean 的 on_start（同步版本）"""
        for name in self._load_order:
            instance = get_instance(name)
            if instance:
                try:
                    method = getattr(instance, 'on_start', None)
                    if method and not inspect.iscoroutinefunction(method):
                        method()
                    logger.debug(f"启动 Bean: {name}")
                except Exception as e:
                    logger.error(f"启动 Bean {name} 失败: {e}")
                    raise

    def shutdown_all(self):
        """逆序执行 on_stop 和 on_destroy（同步版本）"""
        for name in reversed(self._load_order):
            instance = get_instance(name)
            if instance:
                try:
                    on_stop = getattr(instance, 'on_stop', None)
                    on_destroy = getattr(instance, 'on_destroy', None)
                    if on_stop and not inspect.iscoroutinefunction(on_stop):
                        on_stop()
                    if on_destroy and not inspect.iscoroutinefunction(on_destroy):
                        on_destroy()
                    logger.debug(f"关闭 Bean: {name}")
                except Exception as e:
                    logger.error(f"关闭 Bean {name} 失败: {e}")

        self._load_order.clear()

    # ---- 异步 API ----

    async def async_create_all(self):
        """创建所有注册的 Bean（异步版本，支持 async 生命周期）

        1. 处理 @Import：自动注册外部类
        2. 拓扑排序确定创建顺序
        3. 按顺序创建 Bean 并调用 on_init
        """
        all_classes = get_all_classes()

        for name, cls in list(all_classes.items()):
            imports = getattr(cls, '_imports', [])
            for imported_cls in imports:
                if imported_cls.__name__ not in get_all_classes():
                    self.register(imported_cls)

        order = self._resolve_dependency_order()

        for name in order:
            cls = get_class(name)
            try:
                instance = cls()
                register_instance(name, instance)
                self._load_order.append(name)
                await _call_lifecycle(instance, 'on_init')
                logger.debug(f"创建 Bean: {name}")
            except Exception as e:
                logger.error(f"创建 Bean {name} 失败: {e}")
                raise

    async def async_startup_all(self):
        """执行所有 Bean 的 on_start（异步版本）"""
        for name in self._load_order:
            instance = get_instance(name)
            if instance:
                try:
                    await _call_lifecycle(instance, 'on_start')
                    logger.debug(f"启动 Bean: {name}")
                except Exception as e:
                    logger.error(f"启动 Bean {name} 失败: {e}")
                    raise

    async def async_shutdown_all(self):
        """逆序执行 on_stop 和 on_destroy（异步版本）"""
        for name in reversed(self._load_order):
            instance = get_instance(name)
            if instance:
                try:
                    await _call_lifecycle(instance, 'on_stop')
                    await _call_lifecycle(instance, 'on_destroy')
                    logger.debug(f"关闭 Bean: {name}")
                except Exception as e:
                    logger.error(f"关闭 Bean {name} 失败: {e}")

        self._load_order.clear()

    # ---- 查询 API ----

    def get_all_instances(self) -> dict[str, Dough]:
        """获取所有已创建的实例"""
        return get_all_instances()

    def get_all_classes(self) -> dict[str, type]:
        """获取所有注册的类"""
        return get_all_classes()
