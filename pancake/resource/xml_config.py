"""
Pancake XML 启动配置解析器
解析项目根目录的 pancake.xml，提取插件列表和全局配置
"""

import os
import re
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

XML_FILE_PRIMARY = "pancake.xml"


def _resolve_env_vars(value: str) -> str:
    """替换 ${env:VAR_NAME} 为环境变量值"""
    pattern = re.compile(r'\$\{env:([a-zA-Z0-9_.]+)}')

    def replacer(match):
        var_name = match.group(1)
        env_val = os.getenv(var_name)
        if env_val is None:
            logger.warning(f"Environment variable {var_name} not found")
            return match.group(0)
        return env_val

    return pattern.sub(replacer, value)


def _parse_properties(config_elem) -> dict:
    """解析 <config> 下的 <property> 元素"""
    result = {}
    for prop in config_elem.findall("property"):
        name = prop.get("name")
        value = prop.get("value", "")
        if name:
            value = _resolve_env_vars(value)
            # 尝试转换类型
            result[name] = _auto_convert(value)
    return result


def _auto_convert(value: str):
    """自动转换字符串值为 Python 类型"""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _find_xml_file() -> str | None:
    """查找 XML 配置文件，从当前目录向上搜索"""
    d = os.getcwd()
    for _ in range(3):
        primary = os.path.join(d, XML_FILE_PRIMARY)
        if os.path.exists(primary):
            return primary
        d = os.path.dirname(d)
    return None


def load_xml(xml_path: str = None) -> dict:
    """
    加载并解析 pancake.xml

    Returns:
        {
            "plugins": [
                {
                    "name": "web",
                    "source": "ovenware.web",
                    "init_order": 10,
                    "build_order": 0,
                    "enabled": True,
                    "config": {"title": "My App", "port": 8080}
                },
                ...
            ],
            "config": {"log.level": "INFO", ...}
        }
    """
    if xml_path is None:
        xml_path = _find_xml_file()

    if xml_path is None:
        logger.info("No pancake.xml found, using directory scanning mode")
        return {"plugins": [], "config": {}}

    if not os.path.exists(xml_path):
        logger.warning(f"XML config not found: {xml_path}")
        return {"plugins": [], "config": {}}

    logger.info(f"Loading XML config: {xml_path}")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return {"plugins": [], "config": {}}

    result = {"plugins": [], "config": {}}

    # 解析全局配置：支持 <config> 和 <global> 两种写法
    global_config = root.find("config") or root.find("global")
    if global_config is not None:
        result["config"] = _parse_properties(global_config)
        # 支持直接子元素格式：<service.title>xxx</service.title>
        for child in global_config:
            if child.tag != "property" and child.text and child.text.strip():
                key = child.tag
                value = child.text.strip()
                value = _resolve_env_vars(value)
                result["config"][key] = _auto_convert(value)

    # 解析 <plugins>
    plugins_elem = root.find("plugins")
    if plugins_elem is None:
        logger.warning("No <plugins> section found in XML")
        return result

    for plugin_elem in plugins_elem.findall("plugin"):
        name = plugin_elem.get("name")
        source = plugin_elem.get("source")
        if not name:
            logger.warning("Plugin missing name, skipping")
            continue
        if not source:
            # 从 name 推导 source，如 "web" -> "ovenware.web"
            source = f"ovenware.{name}"

        # 解析属性
        init_order = int(plugin_elem.get("init-order", "0"))
        build_order = int(plugin_elem.get("build-order", "0"))
        enabled = plugin_elem.get("enabled", "true").lower() == "true"

        # 解析插件级 <config>
        plugin_config = {}
        plugin_config_elem = plugin_elem.find("config")
        if plugin_config_elem is not None:
            plugin_config = _parse_properties(plugin_config_elem)

        plugin_info = {
            "name": name,
            "source": source,
            "init_order": init_order,
            "build_order": build_order,
            "enabled": enabled,
            "config": plugin_config,
        }
        result["plugins"].append(plugin_info)

    # 按 init_order 排序
    result["plugins"].sort(key=lambda p: p["init_order"])

    logger.info(f"Loaded {len(result['plugins'])} plugins from XML")
    return result
