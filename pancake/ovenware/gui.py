"""
GUI (图形界面) 插件
基于 flet (Flutter) 库，提供装饰器驱动的页面注册

配置项（YAML）：
  client.type: [gui]           # 启用 GUI 客户端
  client.gui.port: 8550        # 端口（web 模式）
  client.gui.view: flet_app    # 视图模式: flet_app / web_browser

可选依赖：pip install flet

使用方法：
    import flet as ft

    @gui_page("/")
    def home(page: ft.Page):
        page.title = "首页"
        page.add(ft.Text("Welcome to Pancake GUI"))

    @gui_page("/users")
    async def users(page: ft.Page):
        mapper = UserMapper()
        users = await mapper.select_list()
        page.add(ft.ListView([ft.Text(u.name) for u in users]))

    @gui_action("refresh")
    async def refresh(page: ft.Page):
        # 更新 UI 组件
        pass
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable

from pancake import oven

logger = logging.getLogger(__name__)


# ============================================================
#  页面信息
# ============================================================

class _PageInfo:
    """存储一个 GUI 页面的元信息"""

    def __init__(self, route: str, func: Callable, title: str = None):
        self.route = route
        self.func = func
        self.title = title
        self.is_async = asyncio.iscoroutinefunction(func)


class _ActionInfo:
    """存储一个 GUI 动作的元信息"""

    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func
        self.is_async = asyncio.iscoroutinefunction(func)


# ============================================================
#  装饰器
# ============================================================

def gui_page(route: str = None, title: str = None):
    """
    GUI 页面装饰器 — 注册一个页面路由

    Args:
        route: 页面路由路径（如 "/"、"/users"）
        title: 页面标题（可选）

    用法：
        @gui_page("/", title="首页")
        def home(page: ft.Page):
            page.add(ft.Text("Hello"))
    """
    def decorator(func: Callable) -> Callable:
        nonlocal route
        if route is None:
            route = f"/{func.__name__}"

        info = _PageInfo(route, func, title)
        registry = oven.pancake_dough.setdefault("GuiPage", {})
        registry[route] = info
        logger.info(f"GUI 页面 {route} 已注册")

        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        wrapper._gui_info = info
        return wrapper
    return decorator


def gui_action(name: str = None):
    """
    GUI 动作装饰器 — 注册一个可复用的 UI 动作

    用法：
        @gui_action("refresh_users")
        async def refresh(page: ft.Page):
            # 更新 UI
            pass
    """
    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__

        info = _ActionInfo(name, func)
        registry = oven.pancake_dough.setdefault("GuiAction", {})
        registry[name] = info
        logger.info(f"GUI 动作 {name} 已注册")

        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        wrapper._gui_info = info
        return wrapper
    return decorator


# ============================================================
#  异步包装
# ============================================================

def _wrap_handler(func: Callable) -> Callable:
    """将异步/同步处理函数包装为统一的 flet 回调"""
    if asyncio.iscoroutinefunction(func):
        def async_wrapper(page):
            return asyncio.run(func(page))
        functools.update_wrapper(async_wrapper, func)
        return async_wrapper
    return func


# ============================================================
#  插件 Main 类
# ============================================================

class Main(InitAction):
    """GUI 插件主类"""

    init_order: int = 50
    build_order: int = 50

    def __init__(self):
        oven.pancake_dough.setdefault("GuiPage", {})
        oven.pancake_dough.setdefault("GuiAction", {})

        # 读取配置
        gui_config = oven.pancake_yaml.get("client.gui", {})
        if isinstance(gui_config, str):
            gui_config = {}
        self.port = int(gui_config.get("port",
                    oven.pancake_yaml.get("client.gui.port", 8550)))
        self.view = gui_config.get("view",
                    oven.pancake_yaml.get("client.gui.view", "flet_app"))

        # 检查是否启用
        self._active = self._is_active()

    def _is_active(self) -> bool:
        """检查 GUI 是否在 client.type 配置中启用"""
        client_type = oven.pancake_yaml.get("client.type", "web")
        if isinstance(client_type, list):
            return "gui" in client_type
        return client_type == "gui"

    @staticmethod
    def check():
        try:
            import flet as ft  # noqa: F401
        except ImportError:
            logger.warning("flet 包未安装，请运行: pip install flet")

    def build(self):
        if not self._active:
            logger.info("GUI 客户端未启用，跳过构建")
            return

        import flet as ft

        pages = oven.pancake_dough.get("GuiPage", {})
        actions = oven.pancake_dough.get("GuiAction", {})

        # 预处理页面处理器
        route_handlers: dict[str, Callable] = {}
        for route, info in pages.items():
            route_handlers[route] = _wrap_handler(info.func)

        # 预处理动作处理器
        action_handlers: dict[str, Callable] = {}
        for name, info in actions.items():
            action_handlers[name] = _wrap_handler(info.func)

        # 存储供 loop_method 使用
        self._route_handlers = route_handlers
        self._action_handlers = action_handlers
        self._default_route = "/" if "/" in route_handlers else (next(iter(route_handlers), None))

        logger.info(f"GUI 插件构建完成 ({len(pages)} 个页面, {len(actions)} 个动作)")

    def _create_app(self):
        """创建 flet 应用入口函数"""
        import flet as ft

        route_handlers = self._route_handlers
        action_handlers = self._action_handlers
        default_route = self._default_route

        def app(page: ft.Page):
            page.title = oven.pancake_yaml.get("service.title", "Pancake GUI")

            def on_route_change(e):
                page.views.clear()
                handler = route_handlers.get(e.route)
                if handler:
                    try:
                        handler(page)
                    except Exception as ex:
                        page.add(ft.Text(f"错误: {ex}", color="red"))
                        logger.error(f"GUI 页面 {e.route} 错误: {ex}")
                else:
                    page.add(ft.Text(f"页面不存在: {e.route}"))
                page.update()

            # 将 action 注册到 page，方便页面内调用
            page.data = {"actions": action_handlers}

            page.on_route_change = on_route_change
            page.go(default_route or "/")

        return app

    def loop_method(self):
        if not self._active:
            return

        import flet as ft

        app = self._create_app()
        logger.info(f"启动 GUI: port={self.port}, view={self.view}")

        # 根据 view 模式选择启动方式
        if self.view == "web_browser":
            ft.app(target=app, port=self.port, view=ft.WEB_BROWSER)
        else:
            ft.app(target=app, port=self.port, view=ft.FLET_APP)


# ============================================================
#  注册到 oven
# ============================================================

oven.muffin_flour["gui_page"] = gui_page
oven.muffin_flour["gui_action"] = gui_action
