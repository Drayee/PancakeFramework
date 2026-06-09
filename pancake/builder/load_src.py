"""用户代码加载模块 — 扫描 src/ 下的 .py 文件并执行"""

import ast
import builtins
import os
import sys

from pancake.registry import get_all_decorators, get_decorator

# 所有 src 文件共享的全局命名空间
_shared_globals = {
    "__builtins__": builtins,
    "__name__": "__not_main__",
}


def scan_py_files(folder="."):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.endswith(".py") and f != os.path.basename(__file__):
                files.append(os.path.abspath(os.path.join(root, f)))
    return files

def parse_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (OSError, IOError, SyntaxError):
        return []

    dirname = os.path.dirname(filepath)
    if dirname not in sys.path:
        sys.path.insert(0, dirname)

    results = []
    all_decorators = get_all_decorators()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        obj_type = "class" if isinstance(node, ast.ClassDef) else "function"
        obj_name = node.name

        # 遍历所有装饰器
        for dec in node.decorator_list:
            dec_name = None
            if isinstance(dec, ast.Name):
                dec_name = dec.id
            elif isinstance(dec, ast.Call) and hasattr(dec.func, 'id'):
                dec_name = dec.func.id

            if dec_name and dec_name in all_decorators:
                results.append((dec_name, obj_type, obj_name, filepath))

        # 检查基类是否在注册表中（如 class User(Struct)）
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name and base_name in all_decorators:
                    results.append((base_name, obj_type, obj_name, filepath))
    return results

def safe_register(filepath):
    """在共享命名空间中执行文件，所有定义对其他文件可见"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except (OSError, IOError):
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    definitions = []
    for node in tree.body:
        if isinstance(node, ast.If):
            if (isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"):
                continue
        definitions.append(node)

    if not definitions:
        return

    new_tree = ast.Module(body=definitions, type_ignores=[])
    ast.fix_missing_locations(new_tree)

    try:
        code = compile(new_tree, filepath, 'exec')
        exec(code, _shared_globals)
    except Exception:
        import traceback
        traceback.print_exc()
        return


def _try_exec(filepath):
    """尝试执行文件，成功返回 True，失败返回 False"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except (OSError, IOError):
        return True

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return True

    definitions = []
    for node in tree.body:
        if isinstance(node, ast.If):
            if (isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"):
                continue
        definitions.append(node)

    if not definitions:
        return True

    new_tree = ast.Module(body=definitions, type_ignores=[])
    ast.fix_missing_locations(new_tree)

    try:
        code = compile(new_tree, filepath, 'exec')
        exec(code, _shared_globals)
        return True
    except NameError:
        return False
    except Exception:
        import traceback
        traceback.print_exc()
        return True


def run():
    from pancake.settings import get_path
    src_dir = get_path("src_dir")
    files = scan_py_files(src_dir)

    # 预解析所有文件，按装饰器的 _load_priority 排序（值越小越先加载，默认 50）
    file_items = []
    for f in files:
        items = parse_file(f)
        if items:
            min_priority = 50
            for dec_name, _, _, _ in items:
                dec_obj = get_decorator(dec_name)
                if dec_obj and hasattr(dec_obj, '_load_priority'):
                    min_priority = min(min_priority, dec_obj._load_priority)
            file_items.append((min_priority, f, items))

    file_items.sort(key=lambda x: x[0])

    # 按文件路径去重，保留优先级最高的条目
    seen = set()
    unique_items = []
    for item in file_items:
        if item[1] not in seen:
            seen.add(item[1])
            unique_items.append(item)

    # 第一轮：按优先级执行，收集 NameError 失败的文件
    pending = []
    for _, path, _ in unique_items:
        if not _try_exec(path):
            pending.append(path)

    # 重试轮：NameError 的文件可能依赖其他文件中定义的类
    # 反复重试直到全部成功或无进展
    while pending:
        still_pending = []
        for path in pending:
            if not _try_exec(path):
                still_pending.append(path)
        if len(still_pending) == len(pending):
            # 无进展，剩余文件有无法解决的依赖
            for path in still_pending:
                safe_register(path)
            break
        pending = still_pending
