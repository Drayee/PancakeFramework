"""
DoughFactory — Bean 工厂
替代原有 oven 模块，统一管理所有 Bean
"""

import logging
from pancake.dough import Dough, Scope

logger = logging.getLogger(__name__)


class DoughFactory:
    """Bean 工厂 — 管理 Bean 的注册、创建、生命周期

    支持多个独立工厂实例
    """

    _factories: dict[str, "DoughFactory"] = {}

    def __init__(self, name: str = "default"):
        self.name = name
        self._classes: dict[str, type] = {}
        self._instances: dict[str, Dough] = {}
        self._load_order: list[str] = []
        DoughFactory._factories[name] = self

    @staticmethod
    def get(name: str = "default") -> "DoughFactory":
        """获取或创建工厂实例"""
        if name not in DoughFactory._factories:
            DoughFactory._factories[name] = DoughFactory(name)
        return DoughFactory._factories[name]

    def register(self, cls: type):
        """注册 Bean 类"""
        name = cls.__name__
        self._classes[name] = cls
        logger.debug(f"注册 Bean: {name}")

    def register_instance(self, name: str, instance: object):
        """注册已创建的实例"""
        self._instances[name] = instance
        logger.debug(f"注册实例: {name}")

    def resolve(self, name: str) -> Dough:
        """获取 Bean 实例"""
        # 已有实例
        if name in self._instances:
            instance = self._instances[name]
            # Prototype 每次返回新实例
            if hasattr(instance, '_scope') and instance._scope == Scope.PROTOTYPE:
                cls = self._classes.get(name)
                if cls:
                    return cls()
            return instance

        # Lazy 创建
        cls = self._classes.get(name)
        if cls is None:
            raise ValueError(f"未注册的 Bean: {name}")

        if cls._scope == Scope.LAZY:
            instance = cls()
            self._instances[name] = instance
            instance.on_init()
            return instance

        raise ValueError(f"Bean {name} 尚未创建，请先调用 create_all()")

    def create_all(self):
        """创建所有注册的 Bean"""
        for name, cls in self._classes.items():
            if cls._scope == Scope.LAZY:
                continue  # Lazy 延迟创建

            try:
                instance = cls()
                self._instances[name] = instance
                self._load_order.append(name)
                instance.on_init()
                logger.debug(f"创建 Bean: {name}")
            except Exception as e:
                logger.error(f"创建 Bean {name} 失败: {e}")
                raise

    def build_all(self):
        """执行所有 Bean 的 build（兼容旧插件）"""
        pass

    def startup_all(self):
        """执行所有 Bean 的 on_start"""
        for name in self._load_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    instance.on_start()
                    logger.debug(f"启动 Bean: {name}")
                except Exception as e:
                    logger.error(f"启动 Bean {name} 失败: {e}")
                    raise

    def shutdown_all(self):
        """逆序执行 on_stop 和 on_destroy"""
        for name in reversed(self._load_order):
            instance = self._instances.get(name)
            if instance:
                try:
                    instance.on_stop()
                    instance.on_destroy()
                    logger.debug(f"关闭 Bean: {name}")
                except Exception as e:
                    logger.error(f"关闭 Bean {name} 失败: {e}")

        self._instances.clear()
        self._load_order.clear()

    def get_all_instances(self) -> dict[str, Dough]:
        """获取所有已创建的实例"""
        return dict(self._instances)

    def get_all_classes(self) -> dict[str, type]:
        """获取所有注册的类"""
        return dict(self._classes)
