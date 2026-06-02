import ast
import builtins
import os
import sys
from pancake import oven

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
    for node in ast.walk(tree):
        # 扫描 类 + 函数（含 async def）
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

            # 匹配 muffin_flour 中的装饰器
            if dec_name in oven.muffin_flour.keys():
                results.append((dec_name, obj_type, obj_name, filepath))
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

    # 收集所有顶级定义
    definitions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
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

    # 将文件中定义的名称注入 builtins，实现跨文件零 import
    for node in definitions:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in _shared_globals:
                builtins.__dict__[node.name] = _shared_globals[node.name]

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
                dec_obj = oven.muffin_flour.get(dec_name)
                if dec_obj and hasattr(dec_obj, '_load_priority'):
                    min_priority = min(min_priority, dec_obj._load_priority)
            file_items.append((min_priority, f, items))

    file_items.sort(key=lambda x: x[0])

    for _, path, _ in file_items:
        safe_register(path)