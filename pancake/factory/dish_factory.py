"""
DishFactory — Bean 工厂
类似 Spring 的 BeanFactory/ApplicationContext，统一管理用户代码的发现、注册、实例化、生命周期。

使用方法：
    factory = DishFactory()
    factory.discover("src")      # 扫描 src/ 发现用户代码
    factory.create_all()         # 实例化所有 Bean
    bean = factory.get("UserService")
    beans = factory.get_by_category("controller")
"""

import ast
import builtins
import inspect
import logging
import os
import sys
from typing import Any, Callable

logger = logging.getLogger(__name__)


class DishFactory:
    """Bean 工厂 — 统一管理用户代码"""

    def __init__(self):
        self._beans: dict[str, Any] = {}            # name -> instance
        self._bean_classes: dict[str, type] = {}     # name -> class
        self._categories: dict[str, list[str]] = {}  # category -> [names]
        self._metadata: dict[str, dict] = {}         # name -> metadata
        self._load_order: list[str] = []             # 加载顺序

    # === 注册 ===

    def register(self, name: str, cls_or_obj: Any, category: str = "bean", **meta):
        """注册 Bean（类或实例）"""
        if inspect.isclass(cls_or_obj):
            self._bean_classes[name] = cls_or_obj
        else:
            self._beans[name] = cls_or_obj

        self._categories.setdefault(category, []).append(name)
        self._metadata[name] = {"category": category, **meta}
        if name not in self._load_order:
            self._load_order.append(name)

    def register_class(self, cls: type, category: str = "bean", **meta):
        """注册类（延迟实例化）"""
        name = cls.__name__
        self.register(name, cls, category=category, **meta)

    def register_instance(self, name: str, obj: Any, category: str = "bean", **meta):
        """注册实例"""
        self.register(name, obj, category=category, **meta)

    # === 查询 ===

    def get(self, name: str) -> Any:
        """按名称获取 Bean"""
        if name in self._beans:
            return self._beans[name]
        if name in self._bean_classes:
            # 延迟实例化
            cls = self._bean_classes[name]
            instance = cls()
            self._beans[name] = instance
            return instance
        return None

    def get_by_type(self, cls: type) -> list[Any]:
        """按类型获取 Bean"""
        result = []
        for name, instance in self._beans.items():
            if isinstance(instance, cls):
                result.append(instance)
        for name, bean_cls in self._bean_classes.items():
            if issubclass(bean_cls, cls) and name not in self._beans:
                instance = self.get(name)
                if instance:
                    result.append(instance)
        return result

    def get_by_category(self, category: str) -> list[Any]:
        """按分类获取（如所有 controller、所有 service）"""
        names = self._categories.get(category, [])
        return [self.get(name) for name in names if self.get(name) is not None]

    def has(self, name: str) -> bool:
        """检查 Bean 是否存在"""
        return name in self._beans or name in self._bean_classes

    def list_all(self) -> list[dict]:
        """列出所有 Bean 的元信息"""
        result = []
        for name in self._load_order:
            meta = self._metadata.get(name, {})
            info = {
                "name": name,
                "category": meta.get("category", "bean"),
                "instantiated": name in self._beans,
            }
            if name in self._bean_classes:
                info["class"] = self._bean_classes[name].__name__
            result.append(info)
        return result

    # === 生命周期 ===

    def create_all(self):
        """实例化所有注册的类，调用 on_init()"""
        from pancake.ovenware.core import Dish

        for name in self._load_order:
            if name in self._beans:
                continue  # 已经是实例
            if name not in self._bean_classes:
                continue

            cls = self._bean_classes[name]
            try:
                instance = cls()
                self._beans[name] = instance

                # 调用 on_init 钩子
                if isinstance(instance, Dish):
                    instance.on_init()

                logger.debug(f"Bean '{name}' 已实例化")
            except Exception as e:
                logger.error(f"Bean '{name}' 实例化失败: {e}")

    async def startup_all(self):
        """调用所有 Bean 的 on_startup()"""
        from pancake.ovenware.core import Dish

        for name in self._load_order:
            instance = self._beans.get(name)
            if instance and isinstance(instance, Dish):
                try:
                    await instance.on_startup()
                except Exception as e:
                    logger.error(f"Bean '{name}' startup 失败: {e}")

    async def shutdown_all(self):
        """逆序调用所有 Bean 的 on_shutdown()，然后 on_destroy()"""
        from pancake.ovenware.core import Dish

        for name in reversed(self._load_order):
            instance = self._beans.get(name)
            if instance and isinstance(instance, Dish):
                try:
                    await instance.on_shutdown()
                except Exception as e:
                    logger.error(f"Bean '{name}' shutdown 失败: {e}")

        for name in reversed(self._load_order):
            instance = self._beans.get(name)
            if instance and isinstance(instance, Dish):
                try:
                    instance.on_destroy()
                except Exception as e:
                    logger.error(f"Bean '{name}' destroy 失败: {e}")

    # === 自动发现 ===

    def discover(self, src_dir: str = "src"):
        """扫描 src/ 目录，发现并注册所有带装饰器的类/函数"""
        from pancake import oven

        if not os.path.isdir(src_dir):
            logger.warning(f"源码目录不存在: {src_dir}")
            return

        from pancake.registry import flour

        files = self._scan_py_files(src_dir)

        # 预解析所有文件，按 _load_priority 排序
        file_items = []
        for filepath in files:
            items = self._parse_file(filepath)
            if items:
                min_priority = 50
                for dec_name, _, _, _ in items:
                    dec_obj = flour.get(dec_name)
                    if dec_obj and hasattr(dec_obj, '_load_priority'):
                        min_priority = min(min_priority, dec_obj._load_priority)
                file_items.append((min_priority, filepath, items))

        file_items.sort(key=lambda x: x[0])

        # 执行文件（注册装饰器）
        shared_globals = {
            "__builtins__": builtins,
            "__name__": "__not_main__",
        }

        for priority, filepath, items in file_items:
            self._safe_register(filepath, shared_globals)

            # 将装饰器注册的类/函数同步到 DishFactory
            for dec_name, obj_type, obj_name, _ in items:
                category = self._decorator_to_category(dec_name)
                if category and obj_name not in self._metadata:
                    # 从 oven.pancake_dough 查找注册的对象
                    obj = self._find_registered_object(dec_name, obj_name)
                    if obj is not None:
                        self.register(obj_name, obj, category=category, decorator=dec_name)

        logger.info(f"DishFactory 发现 {len(self._load_order)} 个 Bean")

    # === 构建 ===

    def build_all(self):
        """构建所有 Bean（调用 @Service 的 build 方法）"""
        from pancake.registry import register_instance

        for name, cls in list(self._bean_classes.items()):
            if hasattr(cls, 'build') and callable(cls.build):
                try:
                    instance = cls.build()
                    if instance:
                        self._beans[name] = instance
                        register_instance(name, instance)
                except Exception as e:
                    logger.error(f"Bean '{name}' 构建失败: {e}")

    # === 内部方法 ===

    @staticmethod
    def _scan_py_files(folder: str) -> list[str]:
        """扫描目录下所有 .py 文件"""
        files = []
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.abspath(os.path.join(root, f)))
        return files

    @staticmethod
    def _parse_file(filepath: str) -> list[tuple]:
        """解析文件中的装饰器"""
        from pancake.registry import flour

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
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            obj_type = "class" if isinstance(node, ast.ClassDef) else "function"
            obj_name = node.name

            for dec in node.decorator_list:
                dec_name = None
                if isinstance(dec, ast.Name):
                    dec_name = dec.id
                elif isinstance(dec, ast.Call) and hasattr(dec.func, 'id'):
                    dec_name = dec.func.id

                if dec_name in flour:
                    results.append((dec_name, obj_type, obj_name, filepath))
        return results

    @staticmethod
    def _safe_register(filepath: str, shared_globals: dict):
        """在共享命名空间中执行文件"""
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
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                definitions.append(node)

        if not definitions:
            return

        new_tree = ast.Module(body=definitions, type_ignores=[])
        ast.fix_missing_locations(new_tree)

        try:
            code = compile(new_tree, filepath, 'exec')
            exec(code, shared_globals)
        except Exception:
            import traceback
            traceback.print_exc()
            return

        # 注入 builtins
        for node in definitions:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in shared_globals:
                    builtins.__dict__[node.name] = shared_globals[node.name]

    @staticmethod
    def _decorator_to_category(dec_name: str) -> str | None:
        """装饰器名 -> Bean 分类"""
        mapping = {
            "Service": "service",
            "Mapper": "mapper",
            "get_controller": "controller",
            "post_controller": "controller",
            "put_controller": "controller",
            "delete_controller": "controller",
            "patch_controller": "controller",
            "page_controller": "controller",
            "websocket_controller": "controller",
            "cui_command": "command",
            "gui_page": "page",
            "gui_action": "page",
            "event_node": "event",
            "on_event": "event",
            "remote_node": "remote",
            "lifecycle_node": "lifecycle",
            "langgraph_node": "workflow",
            "langgraph_edge": "workflow",
        }
        return mapping.get(dec_name)

    @staticmethod
    def _find_registered_object(dec_name: str, obj_name: str) -> Any:
        """从 registry 查找注册的对象"""
        from pancake.registry import get_class
        return get_class(obj_name)


# 模块级默认实例
_dish_factory = DishFactory()


def get_dish_factory() -> DishFactory:
    """获取全局 DishFactory 实例"""
    return _dish_factory
