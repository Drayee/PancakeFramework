import sys

from pancake import oven
from pancake.initialize import check_dlc

import importlib
import inspect
import logging
import os

logger = logging.getLogger(__name__)


def _load_from_xml():
    """从 XML 配置加载插件列表"""
    plugins = oven.pancake_xml.get("plugins", [])
    if not plugins:
        return None  # 无 XML 配置，回退到目录扫描

    main_classes = {}

    for plugin_info in plugins:
        name = plugin_info["name"]
        source = plugin_info["source"]
        enabled = plugin_info.get("enabled", True)
        init_order = plugin_info.get("init_order", 0)
        build_order = plugin_info.get("build_order", 0)

        # 导入插件模块（无论是否启用都需要导入，以注册装饰器）
        try:
            plugin = importlib.import_module(source)
        except ImportError as e:
            if enabled:
                logger.error(f"Failed to import plugin {name} ({source}): {e}")
                sys.exit(1)
            else:
                logger.debug(f"Disabled plugin {name} not available: {e}")
                continue

        # 收集模块中的公开成员
        all_items = {}
        for attr_name, member in inspect.getmembers(plugin):
            if (
                (not attr_name.startswith("_"))
                and (inspect.isclass(member) or inspect.isfunction(member))
                and (member.__module__ == plugin.__name__ or member.__module__.startswith(plugin.__name__ + "."))
            ):
                all_items[attr_name] = member

        # 注册装饰器（无论是否启用都注册）
        for item_name, obj in all_items.items():
            if item_name.startswith("_"):
                continue
            if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                continue  # Main 类下面单独处理
            oven.muffin_flour[item_name] = obj

        # 注册 Main 类（仅启用时）
        if enabled:
            for item_name, obj in all_items.items():
                if item_name.startswith("_"):
                    continue
                if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                    effective_init = init_order
                    effective_build = build_order

                    oven.muffin_egg["BuildOrder"].append([name, effective_build])
                    oven.muffin_egg["InitOrder"].append([name, effective_init])
                    main_classes[name] = obj
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
    # 单文件插件
    plugin_files = [f[:-3] for f in entries if f.endswith(".py") and f not in ["__init__.py"]]
    # 子包插件（目录含 __init__.py）
    plugin_dirs = [d for d in entries
                   if os.path.isdir(os.path.join(dlc_dir, d))
                   and os.path.exists(os.path.join(dlc_dir, d, "__init__.py"))
                   and not d.startswith("_")]
    plugin_names = plugin_files + plugin_dirs

    main_classes = {}

    for plugin_name in plugin_names:
        if plugin_name in oven.pancake_yaml.get("framework.disable_dlc", []):
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

        # 加载 all_items 中的所有 修饰器和 main 类
        for decorator in all_items.keys():
            if not decorator.startswith("_"):
                obj = all_items[decorator]
                if inspect.isclass(obj) and hasattr(obj, 'build') and hasattr(obj, 'init_order'):
                    oven.muffin_egg["BuildOrder"].append([plugin_name, all_items[decorator].build_order])
                    oven.muffin_egg["InitOrder"].append([plugin_name, all_items[decorator].init_order])
                    main_classes[plugin_name] = all_items[decorator]
                    continue
                oven.muffin_flour[decorator] = all_items[decorator]

    return main_classes


def run():
    """加载插件：优先 XML 配置，回退到目录扫描"""
    has_xml = bool(oven.pancake_xml.get("plugins"))

    if has_xml:
        logger.info("Loading plugins from XML config")
        main_classes = _load_from_xml()
    else:
        logger.info("No XML config, scanning ovenware directory")
        main_classes = _load_from_directory()

    oven.muffin_egg["BuildOrder"].sort(key=lambda x: x[1], reverse=True)
    oven.muffin_egg["InitOrder"].sort(key=lambda x: x[1])

    for plugin_name in oven.muffin_egg["InitOrder"]:
        try:
            check_dlc(main_classes[plugin_name[0]].check)
        except AttributeError:
            pass
        except Exception as e:
            logger.error(f"Plugin check failed for {plugin_name[0]}: {e}")
            import sys
            sys.exit(1)

        new_main = main_classes[plugin_name[0]]()

        oven.muffin_egg["Builder"][plugin_name[0]] = new_main.build

        # 尝试获取 loop_method，verify_method
        try:
            oven.muffin_egg["LoopMethod"][plugin_name[0]] = new_main.loop_method
        except AttributeError:
            pass
        try:
            oven.muffin_egg["VerifyMethod"][plugin_name[0]] = new_main.verify
        except AttributeError:
            pass
