"""
插件加载模块
自动发现并加载 ovenware/ 下的插件，注册装饰器到 registry
"""

import sys
import importlib
import inspect
import logging
import os

from pancake.registry import register_decorator
from pancake.factory.dough_factory import DoughFactory
from pancake import settings

logger = logging.getLogger(__name__)


def _load_from_xml():
    """从 XML 配置加载插件列表"""
    plugins = settings.get("_xml_plugins", [])
    if not plugins:
        return None

    main_classes = {}

    for plugin_info in plugins:
        name = plugin_info["name"]
        source = plugin_info["source"]
        enabled = plugin_info.get("enabled", True)
        init_order = plugin_info.get("init_order", 0)
        build_order = plugin_info.get("build_order", 0)

        try:
            plugin = importlib.import_module(source)
        except ImportError as e:
            if enabled:
                logger.error(f"Failed to import plugin {name} ({source}): {e}")
                sys.exit(1)
            else:
                logger.debug(f"Disabled plugin {name} not available: {e}")
                continue

        all_items = {}
        for attr_name, member in inspect.getmembers(plugin):
            if (
                (not attr_name.startswith("_"))
                and (inspect.isclass(member) or inspect.isfunction(member))
                and (member.__module__ == plugin.__name__ or member.__module__.startswith(plugin.__name__ + "."))
            ):
                all_items[attr_name] = member

        # 注册装饰器到 registry（无论是否启用都注册）
        for item_name, obj in all_items.items():
            if item_name.startswith("_"):
                continue
            if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                continue
            register_decorator(item_name, obj)

        # 注册 Main 类（仅启用时）
        if enabled:
            for item_name, obj in all_items.items():
                if item_name.startswith("_"):
                    continue
                if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                    main_classes[name] = {
                        "class": obj,
                        "init_order": init_order,
                        "build_order": build_order,
                    }
                    break
            else:
                logger.info(f"Plugin {name} loaded (no Main class)")
        else:
            logger.info(f"Plugin {name} disabled (decorators still loaded)")

    return main_classes


def _load_from_directory():
    """从 ovenware 目录扫描加载插件（回退模式）"""
    dlc_dir = os.path.join(os.path.dirname(__file__), "../", "ovenware")
    entries = os.listdir(dlc_dir)
    plugin_files = [f[:-3] for f in entries if f.endswith(".py") and f not in ["__init__.py"]]
    plugin_dirs = [d for d in entries
                   if os.path.isdir(os.path.join(dlc_dir, d))
                   and os.path.exists(os.path.join(dlc_dir, d, "__init__.py"))
                   and not d.startswith("_")]
    plugin_names = plugin_files + plugin_dirs

    disable_dlc = settings.get("framework.disable_dlc", [])
    main_classes = {}

    for plugin_name in plugin_names:
        if plugin_name in disable_dlc:
            continue
        plugin = importlib.import_module(f"ovenware.{plugin_name}")
        all_items = {}
        for name, member in inspect.getmembers(plugin):
            if (
                (not name.startswith("_"))
                and (inspect.isclass(member) or inspect.isfunction(member))
                and (member.__module__ == plugin.__name__ or member.__module__.startswith(plugin.__name__ + "."))
            ):
                all_items[name] = member

        for decorator in all_items.keys():
            if not decorator.startswith("_"):
                obj = all_items[decorator]
                if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                    main_classes[plugin_name] = {
                        "class": obj,
                        "init_order": getattr(obj, 'init_order', 0),
                        "build_order": getattr(obj, 'build_order', 0),
                    }
                    continue
                register_decorator(decorator, obj)

    return main_classes


def run():
    """加载插件：优先 XML 配置，回退到目录扫描"""
    has_xml = bool(settings.get("_xml_plugins"))

    if has_xml:
        logger.info("Loading plugins from XML config")
        main_classes = _load_from_xml()
    else:
        logger.info("No XML config, scanning ovenware directory")
        main_classes = _load_from_directory()

    # 按 init_order 排序，初始化插件
    sorted_plugins = sorted(main_classes.items(), key=lambda x: x[1]["init_order"])

    for plugin_name, plugin_info in sorted_plugins:
        cls = plugin_info["class"]

        try:
            instance = cls()
        except Exception as e:
            logger.error(f"Plugin {plugin_name} init failed: {e}")
            sys.exit(1)

        # 检查 check 方法
        if hasattr(instance, 'check'):
            try:
                if not instance.check():
                    logger.info(f"Plugin {plugin_name} check failed, skipping")
                    continue
            except Exception as e:
                logger.error(f"Plugin check failed for {plugin_name}: {e}")
                sys.exit(1)

        # 注册到 DoughFactory
        factory = DoughFactory.get()
        factory.register_instance(plugin_name, instance)

        logger.info(f"Plugin {plugin_name} loaded (init_order={plugin_info['init_order']})")
