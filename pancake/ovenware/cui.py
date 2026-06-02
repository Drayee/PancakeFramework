"""
CUI (命令行界面) 插件
基于 click 库，提供装饰器驱动的 CLI 命令注册

配置项（YAML）：
  client.type: [cui]           # 启用 CUI 客户端
  client.cui.app_name: myapp   # 应用名称
  client.cui.version: "1.0.0"  # 版本号

可选依赖：pip install click

使用方法：
    @cui_command("greet", help="打招呼")
    @cui_option("--name", "-n", default="World", help="名字")
    def greet(name: str):
        click.echo(f"Hello, {name}!")

    @cui_command("migrate", help="执行数据库迁移")
    async def migrate():
        await do_migration()
        click.echo("迁移完成")
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable

from pancake import oven

logger = logging.getLogger(__name__)


# ============================================================
#  命令参数收集器
# ============================================================

class _CommandInfo:
    """存储一个 CLI 命令的元信息"""

    def __init__(self, name: str, func: Callable, help: str = None):
        self.name = name
        self.func = func
        self.help = help or func.__doc__
        self.params: list = []  # click.Argument / click.Option
        self.is_async = asyncio.iscoroutinefunction(func)


# ============================================================
#  装饰器
# ============================================================

def cui_command(name: str = None, help: str = None, **kwargs):
    """
    CLI 命令装饰器 — 注册一个子命令

    Args:
        name: 命令名称（默认使用函数名）
        help: 帮助文本
        **kwargs: 传递给 click.Command 的额外参数
    """
    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__.replace("_", "-")

        info = _CommandInfo(name, func, help)

        # 如果函数有 click 参数装饰器标记，收集它们
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        info.params = func._cui_params

        registry = oven.pancake_dough.setdefault("CuiCommand", {})
        registry[name] = info
        logger.info(f"CUI 命令 {name} 已注册")

        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        wrapper._cui_info = info
        return wrapper
    return decorator


def cui_option(*param_decls, **kwargs):
    """
    CLI 选项装饰器 — 为命令添加 --option 参数

    用法：
        @cui_command("greet")
        @cui_option("--name", "-n", default="World", help="名字")
        def greet(name: str):
            click.echo(f"Hello {name}")
    """
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Option(param_decls, **kwargs))
        return func
    return decorator


def cui_argument(*param_decls, **kwargs):
    """
    CLI 参数装饰器 — 为命令添加 positional argument

    用法：
        @cui_command("process")
        @cui_argument("filename", type=click.Path(exists=True))
        def process(filename: str):
            click.echo(f"Processing {filename}")
    """
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Argument(param_decls, **kwargs))
        return func
    return decorator


# ============================================================
#  异步命令包装
# ============================================================

def _make_click_callback(info: _CommandInfo) -> Callable:
    """将注册的命令函数包装为 click 可调用的回调"""
    import click

    if info.is_async:
        @functools.wraps(info.func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(info.func(*args, **kwargs))
        return sync_wrapper
    else:
        return info.func


# ============================================================
#  插件 Main 类
# ============================================================

class Main(InitAction):
    """CUI 插件主类"""

    init_order: int = 50
    build_order: int = 50

    def __init__(self):
        oven.pancake_dough.setdefault("CuiCommand", {})

        # 读取配置
        cui_config = oven.pancake_yaml.get("client.cui", {})
        if isinstance(cui_config, str):
            cui_config = {}
        self.app_name = cui_config.get("app_name",
                        oven.pancake_yaml.get("client.cui.app_name", "app"))
        self.version = cui_config.get("version",
                       oven.pancake_yaml.get("client.cui.version", "0.1.0"))

        # 检查是否启用
        self._active = self._is_active()

    def _is_active(self) -> bool:
        """检查 CUI 是否在 client.type 配置中启用"""
        client_type = oven.pancake_yaml.get("client.type", "web")
        if isinstance(client_type, list):
            return "cui" in client_type
        return client_type == "cui"

    @staticmethod
    def check():
        try:
            import click  # noqa: F401
        except ImportError:
            logger.warning("click 包未安装，请运行: pip install click")

    def build(self):
        if not self._active:
            logger.info("CUI 客户端未启用，跳过构建")
            return

        import click

        self.cli = click.Group(
            name=self.app_name,
            help=f"{self.app_name} v{self.version}",
        )

        commands = oven.pancake_dough.get("CuiCommand", {})
        for name, info in commands.items():
            callback = _make_click_callback(info)
            cmd = click.Command(
                name=info.name,
                callback=callback,
                params=info.params,
                help=info.help,
            )
            self.cli.add_command(cmd)
            logger.debug(f"CUI 命令构建: {info.name}")

        logger.info(f"CUI 插件构建完成 ({len(commands)} 个命令)")

    def loop_method(self):
        if not self._active:
            return

        import click
        logger.info(f"启动 CUI: {self.app_name}")
        try:
            self.cli(standalone_mode=False)
        except (click.exceptions.Exit, SystemExit):
            pass


# ============================================================
#  注册到 oven
# ============================================================

oven.muffin_flour["cui_command"] = cui_command
oven.muffin_flour["cui_option"] = cui_option
oven.muffin_flour["cui_argument"] = cui_argument
