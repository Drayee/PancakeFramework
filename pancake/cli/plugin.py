"""插件管理命令：plugin list/add/remove/clear"""

import ast
import os
import sys
import xml.etree.ElementTree as ET


def _find_ovenware_dir():
    """找到 ovenware 目录"""
    dlc_dir = os.path.join(os.path.dirname(__file__), "..", "ovenware")
    if os.path.isdir(dlc_dir):
        return dlc_dir
    return None


def _get_disabled_plugins():
    """从 pancake.xml 获取禁用的插件列表"""
    disabled = set()
    xml_path = os.path.join(os.getcwd(), "pancake.xml")
    if not os.path.exists(xml_path):
        return disabled
    try:
        tree = ET.parse(xml_path)
        for plugin in tree.getroot().findall(".//plugin"):
            name = plugin.get("name")
            enabled = plugin.get("enabled", "true").lower()
            if name and enabled == "false":
                disabled.add(name)
    except Exception:
        pass
    return disabled


def cmd_plugin_list(args):
    """列出可用插件"""
    ovenware_dir = _find_ovenware_dir()
    if not ovenware_dir:
        print("错误: 找不到 ovenware 目录")
        sys.exit(1)

    disabled = _get_disabled_plugins()

    entries = os.listdir(ovenware_dir)
    plugins = []

    for entry in sorted(entries):
        full = os.path.join(ovenware_dir, entry)
        is_package = os.path.isdir(full) and os.path.exists(os.path.join(full, "__init__.py"))
        is_module = entry.endswith(".py") and entry != "__init__.py"

        if not is_package and not is_module:
            continue

        name = entry.replace(".py", "")
        if name.startswith("_"):
            continue

        init_order = "-"
        try:
            if is_package:
                mod_path = os.path.join(full, "__init__.py")
            else:
                mod_path = full
            with open(mod_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id == "init_order":
                                    if isinstance(item.value, ast.Constant):
                                        init_order = str(item.value.value)
        except Exception:
            pass

        enabled = name not in disabled
        status = "enabled" if enabled else "disabled"
        plugins.append((name, init_order, status))

    if not plugins:
        print("未找到插件")
        return

    print(f"{'插件名':<25} {'init_order':<12} {'状态':<10}")
    print("-" * 50)
    for name, order, status in plugins:
        print(f"{name:<25} {order:<12} {status:<10}")


def cmd_plugin_add(args):
    """添加插件到 pancake.xml"""
    name = args.name
    xml_path = os.path.join(os.getcwd(), "pancake.xml")

    if not os.path.exists(xml_path):
        print("错误: 当前目录没有 pancake.xml")
        sys.exit(1)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"错误: XML 解析失败: {e}")
        sys.exit(1)

    plugins_elem = root.find("plugins")
    if plugins_elem is None:
        plugins_elem = ET.SubElement(root, "plugins")

    for plugin in plugins_elem.findall("plugin"):
        if plugin.get("name") == name:
            print(f"插件 '{name}' 已存在于 pancake.xml")
            return

    ET.SubElement(plugins_elem, "plugin", name=name)

    ET.indent(tree, space="    ")
    tree.write(xml_path, encoding="UTF-8", xml_declaration=True)
    print(f"已添加插件 '{name}' 到 pancake.xml")


def cmd_plugin_remove(args):
    """从 pancake.xml 移除指定插件"""
    name = args.name
    xml_path = os.path.join(os.getcwd(), "pancake.xml")

    if not os.path.exists(xml_path):
        print("错误: 当前目录没有 pancake.xml")
        sys.exit(1)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"错误: XML 解析失败: {e}")
        sys.exit(1)

    found = False

    plugins_elem = root.find("plugins")
    if plugins_elem is not None:
        for plugin in plugins_elem.findall("plugin"):
            if plugin.get("name") == name:
                plugins_elem.remove(plugin)
                found = True
                break
        if len(plugins_elem) == 0:
            root.remove(plugins_elem)

    deps_elem = root.find("dependencies")
    if deps_elem is not None:
        for dep in deps_elem.findall("dependency"):
            artifact = dep.find("artifactId")
            if artifact is not None and artifact.text == name:
                deps_elem.remove(dep)
                found = True
                break
        if len(deps_elem) == 0:
            root.remove(deps_elem)

    if not found:
        print(f"插件 '{name}' 不存在于 pancake.xml")
        return

    ET.indent(tree, space="    ")
    tree.write(xml_path, encoding="UTF-8", xml_declaration=True)
    print(f"已从 pancake.xml 移除插件 '{name}'")


def cmd_plugin_clear(args):
    """清空 pancake.xml 中的所有插件"""
    xml_path = os.path.join(os.getcwd(), "pancake.xml")

    if not os.path.exists(xml_path):
        print("错误: 当前目录没有 pancake.xml")
        sys.exit(1)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"错误: XML 解析失败: {e}")
        sys.exit(1)

    count = 0

    plugins_elem = root.find("plugins")
    if plugins_elem is not None:
        count += len(plugins_elem.findall("plugin"))
        root.remove(plugins_elem)

    deps_elem = root.find("dependencies")
    if deps_elem is not None:
        dep_count = len(deps_elem.findall("dependency"))
        count += dep_count
        root.remove(deps_elem)

    if count == 0:
        print("pancake.xml 中没有插件")
        return

    ET.indent(tree, space="    ")
    tree.write(xml_path, encoding="UTF-8", xml_declaration=True)
    print(f"已清空所有插件 ({count} 个)")
