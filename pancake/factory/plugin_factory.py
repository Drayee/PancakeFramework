"""
PluginFactory — 插件工厂
统一管理插件的注册、发现、创建、生命周期。

使用方法：
    factory = PluginFactory()
    factory.discover()                    # 扫描 ovenware/ 注册所有 Main 类
    factory.create_all(dependencies)      # 按 init_order 创建实例 + check()
    factory.build_all()                   # 按 build_order 执行 build()
    await factory.startup_all()           # 执行 startup()
    await factory.shutdown_all()          # 逆序执行 shutdown()
"""

import importlib
import inspect
import logging
import os
from typing import Any, Callable

from pancake import oven
from pancake.ovenware import InitAction

logger = logging.getLogger(__name__)


class PluginFactory:
    """插件工厂 — 统一管理插件的注册、创建、生命周期"""

    def __init__(self):
        self._registry: dict[str, type[InitAction]] = {}  # name -> class
        self._instances: dict[str, InitAction] = {}        # name -> instance
        self._load_order: list[str] = []                   # init_order 排序后的名称
        self._build_order: list[str] = []                  # build_order 排序后的名称

    # === 注册 ===

    def register(self, name: str, plugin_cls: type[InitAction]):
        """注册插件类到工厂"""
        self._registry[name] = plugin_cls

    # === 发现 ===

    def discover(self):
        """通过 entry points 发现已安装的插件"""
        from importlib.metadata import entry_points

        eps = entry_points(group="pancake.plugins")

        for ep in eps:
            name = ep.name

            # 检查是否被禁用
            disabled = oven.pancake_yaml.get("framework.disable_dlc", [])
            if name in disabled:
                logger.debug(f"插件 {name} 已禁用，跳过")
                continue

            try:
                plugin_cls = ep.load()
                self.register(name, plugin_cls)
                logger.debug(f"发现插件: {name}")
            except Exception as e:
                logger.debug(f"无法加载插件 {name}: {e}")

        logger.info(f"发现 {len(self._registry)} 个插件")

    # === 创建 ===

    def create_all(self, dependencies: list[dict] = None):
        """从依赖列表创建所有插件实例，按 init_order 排序"""
        # 确定要加载的插件
        if dependencies:
            plugin_names = {
                dep["artifactId"] for dep in dependencies
                if dep.get("groupId") == "io.pancake"
            }
            # embed 总是加载
            plugin_names.add("embed")
        else:
            plugin_names = set(self._registry.keys())

        # 按 init_order 排序
        sorted_plugins = sorted(
            [(name, self._registry[name]) for name in plugin_names if name in self._registry],
            key=lambda x: x[1].init_order
        )

        self._load_order = []

        for name, cls in sorted_plugins:
            # 1. 实例化
            try:
                instance = cls()
            except Exception as e:
                logger.error(f"插件 {name} 实例化失败: {e}")
                continue

            # 2. check()
            try:
                if not instance.check():
                    logger.warning(f"插件 {name} 环境检查未通过，已跳过")
                    continue
            except Exception as e:
                logger.error(f"插件 {name} 环境检查失败: {e}")
                continue

            # 3. 注册实例
            self._instances[name] = instance
            self._load_order.append(name)

            # 4. 注册装饰器（无论是否启用都注册）
            self._register_decorators(name, cls)

            logger.debug(f"插件 {name} 已创建")

        logger.info(f"加载 {len(self._load_order)} 个插件")

    # === 构建 ===

    def build_all(self):
        """按 build_order 执行所有插件的 build()"""
        # 按 build_order 排序
        sorted_names = sorted(
            self._load_order,
            key=lambda name: self._instances[name].build_order,
            reverse=True  # build_order 值大的先执行（与原逻辑一致）
        )

        for name in sorted_names:
            instance = self._instances[name]
            try:
                instance.build()
                logger.debug(f"插件 {name} build 完成")
            except Exception as e:
                logger.error(f"插件 {name} build 失败: {e}")

    # === 生命周期 ===

    async def startup_all(self):
        """按顺序执行所有 startup()"""
        for name in self._load_order:
            instance = self._instances[name]
            try:
                await instance.startup()
            except Exception as e:
                logger.error(f"插件 {name} startup 失败: {e}")

    async def shutdown_all(self):
        """逆序执行所有 shutdown()"""
        for name in reversed(self._load_order):
            instance = self._instances[name]
            try:
                await instance.shutdown()
            except Exception as e:
                logger.error(f"插件 {name} shutdown 失败: {e}")

    def get_loop_methods(self) -> dict[str, Callable]:
        """返回所有注册了 loop_method 的插件"""
        result = {}
        for name in self._load_order:
            instance = self._instances[name]
            # 检查是否重写了 loop_method
            if instance.loop_method.__func__ is not InitAction.loop_method:
                result[name] = instance.loop_method
        return result

    def get_startup_hooks(self) -> list[Callable]:
        """返回所有注册了 startup 的插件"""
        result = []
        for name in self._load_order:
            instance = self._instances[name]
            if instance.startup.__func__ is not InitAction.startup:
                result.append(instance.startup)
        return result

    def get_shutdown_hooks(self) -> list[Callable]:
        """返回所有注册了 shutdown 的插件（逆序）"""
        result = []
        for name in reversed(self._load_order):
            instance = self._instances[name]
            if instance.shutdown.__func__ is not InitAction.shutdown:
                result.append(instance.shutdown)
        return result

    def get_info(self) -> list[dict]:
        """返回所有已加载插件的元信息"""
        return [
            self._instances[name].get_info()
            for name in self._load_order
        ]

    def get_instance(self, name: str) -> InitAction | None:
        """按名称获取插件实例"""
        return self._instances.get(name)

    # === 内部方法 ===

    def _register_decorators(self, name: str, cls: type):
        """注册插件模块中的装饰器到 muffin_flour"""
        # 获取插件类所在的模块
        module_name = cls.__module__
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return

        for attr_name, member in inspect.getmembers(module):
            if (
                not attr_name.startswith("_")
                and (inspect.isclass(member) or inspect.isfunction(member))
                and (member.__module__ == module.__name__ or member.__module__.startswith(module.__name__ + "."))
            ):
                # 跳过 Main 类
                if inspect.isclass(member) and hasattr(member, 'build') and hasattr(member, 'init_order'):
                    continue
                if attr_name not in oven.muffin_flour:
                    oven.muffin_flour[attr_name] = member


# 模块级默认实例
_plugin_factory = PluginFactory()


def get_plugin_factory() -> PluginFactory:
    """获取全局 PluginFactory 实例"""
    return _plugin_factory
