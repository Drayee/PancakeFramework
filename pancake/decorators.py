"""
Decorators — 框架装饰器
提供 @DoughDecorator、@Singleton、@Prototype、@Lazy、@Maker、@noMaker、
@inject、@Config、@DependsOn、@Import 等声明式装饰器
"""

import functools
import inspect
from pancake.dough import Scope


# ---- 类装饰器 ----


def DoughDecorator(cls):
    """@Dough — 标记类为 Bean"""
    cls._scope = Scope.SINGLETON
    return cls


def Singleton(cls):
    """@Singleton — 单例作用域"""
    cls._scope = Scope.SINGLETON
    return cls


def Prototype(cls):
    """@Prototype — 每次获取创建新实例"""
    cls._scope = Scope.PROTOTYPE
    return cls


def Lazy(cls):
    """@Lazy — 延迟初始化"""
    cls._scope = Scope.LAZY
    cls._lazy = True
    return cls


# ---- 方法装饰器 ----


def Maker(func):
    """@Maker — 标记方法返回值为 Bean"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper._is_maker = True
    return wrapper


def noMaker(func):
    """@noMaker — 排除方法，不自动注册"""
    func._no_maker = True
    return func


# ---- 注入装饰器 ----


def _resolve_inject_params(func, kwargs):
    """解析并注入参数（共用逻辑）"""
    hints = {}
    for pname, param in inspect.signature(func).parameters.items():
        if param.annotation is not inspect.Parameter.empty:
            ann = param.annotation
            if isinstance(ann, str):
                try:
                    ann = eval(ann, getattr(func, '__globals__', {}))
                except Exception:
                    pass
            hints[pname] = ann

    for param_name, param_type in hints.items():
        if param_name in kwargs:
            continue
        if param_name == "self" or param_name == "cls":
            continue
        if param_type and hasattr(param_type, '__name__'):
            from pancake.factory.dough_factory import DoughFactory
            try:
                kwargs[param_name] = DoughFactory.get().resolve(param_type.__name__)
            except ValueError:
                pass
    return kwargs


def inject(func):
    """@inject — 自动注入依赖

    从 DoughFactory 解析参数类型对应的 Bean。
    自动检测被装饰函数是否为 async，返回对应的 wrapper。
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            kwargs = _resolve_inject_params(func, kwargs)
            return await func(*args, **kwargs)

        async_wrapper.__annotations__ = {}
        if hasattr(async_wrapper, '__wrapped__'):
            delattr(async_wrapper, '__wrapped__')
        async_wrapper.__signature__ = inspect.Signature()
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            kwargs = _resolve_inject_params(func, kwargs)
            return func(*args, **kwargs)

        sync_wrapper.__annotations__ = {}
        if hasattr(sync_wrapper, '__wrapped__'):
            delattr(sync_wrapper, '__wrapped__')
        sync_wrapper.__signature__ = inspect.Signature()
        return sync_wrapper


# ---- 配置装饰器 ----


def Config(cls):
    """@Config — 从配置注入 Struct 字段"""
    original_on_init = cls.on_init

    @functools.wraps(original_on_init)
    def new_on_init(self):
        from pancake import settings
        for field_name in getattr(cls, '__dataclass_fields__', {}):
            if field_name.startswith("_"):
                continue
            config_key = f"{cls.__name__.lower()}.{field_name}"
            value = settings.get(config_key)
            if value is not None:
                setattr(self, field_name, value)
        original_on_init(self)

    cls.on_init = new_on_init
    return cls


# ---- 依赖声明装饰器 ----


def DependsOn(*deps: str):
    """@DependsOn — 声明 Bean 依赖

    告知 DoughFactory 在创建该 Bean 之前，
    必须先创建指定的依赖 Bean。

    Usage:
        @DependsOn("DatabaseService", "CacheService")
        class MyService(Dough): ...
    """
    def decorator(cls):
        cls._depends_on = list(deps)
        return cls
    return decorator


def Import(*classes: type):
    """@Import — 导入外部类到工厂

    在 DoughFactory.create_all() 阶段，自动将指定的外部类
    注册到工厂中，无需手动 register。

    Usage:
        @Import(DatabaseService, CacheService)
        class AppConfig(Configuration): ...
    """
    def decorator(cls):
        cls._imports = list(classes)
        return cls
    return decorator


# ---- 类型转换装饰器 ----


def _check_dough_type(cls, target_type):
    """检查类是否已应用其他类型装饰器，防止冲突"""
    existing = getattr(cls, '_dough_type', None)
    if existing and existing != target_type:
        raise TypeError(
            f"类 {cls.__name__} 已应用 @{existing} 装饰器，"
            f"不能同时应用 @{target_type} 装饰器"
        )


def _convert_class(cls, *bases, dough_type=None):
    """将普通类转换为继承指定基类的 Dough 子类"""
    from pancake.dough import DoughMeta

    # 冲突检查
    if dough_type:
        _check_dough_type(cls, dough_type)

    # 已经是目标类型则跳过
    for base in bases:
        if isinstance(cls, type(base)):
            if dough_type:
                cls._dough_type = dough_type
            return cls

    # 确保使用 DoughMeta 元类
    if not isinstance(cls, DoughMeta):
        # 创建新的子类，继承原类和目标基类
        new_cls = type(cls.__name__, (cls,) + bases, {
            '__module__': cls.__module__,
            '__qualname__': cls.__qualname__,
            '__doc__': cls.__doc__,
        })
    else:
        # 已经是 Dough 子类，动态添加基类
        cls.__bases__ = bases + cls.__bases__
        new_cls = cls

    if dough_type:
        new_cls._dough_type = dough_type
    return new_cls


def service(cls):
    """@service — 将类转换为 Service（类似 Spring @Service）"""
    from pancake.base.service import Service
    return _convert_class(cls, Service, dough_type="service")


def configuration(cls):
    """@configuration — 将类转换为 Configuration（类似 Spring @Configuration）"""
    from pancake.base.configuration import Configuration
    return _convert_class(cls, Configuration, dough_type="configuration")


def function(func):
    """@function — 将函数转换为 Function 类（类似 Spring @Bean 方法）

    自动添加 @inject 注入依赖，包装为 Function 子类。

    Usage:
        @function
        def my_func(service: MyService) -> str:
            return service.get_data()

        # 使用:
        result = my_func()
    """
    from pancake.base.function import Function

    # 对函数应用 inject
    injected_func = inject(func)

    # 动态创建 Function 子类
    class_name = ''.join(word.capitalize() for word in func.__name__.split('_'))

    def call(self, *args, **kwargs):
        return injected_func(*args, **kwargs)

    new_cls = type(class_name, (Function,), {
        'call': call,
        '__module__': func.__module__,
        '__qualname__': func.__qualname__,
        '__doc__': func.__doc__,
        '_dough_type': 'function',
    })

    return new_cls


def struct(cls):
    """@struct — 将类转换为 Struct（类似 Spring @Component + dataclass）"""
    from pancake.base.struct import Struct
    from dataclasses import dataclass

    # 先应用 dataclass，再转换类型
    cls = dataclass(cls)
    new_cls = _convert_class(cls, Struct, dough_type="struct")
    return new_cls


# ---- 自动注册到 muffin_flour ----

def _register_to_muffin():
    """将所有装饰器注册到 muffin_flour，供 DoughMeta 零 import 注入"""
    from pancake.oven.muffin import muffin_flour
    muffin_flour["DoughDecorator"] = DoughDecorator
    muffin_flour["Singleton"] = Singleton
    muffin_flour["Prototype"] = Prototype
    muffin_flour["Lazy"] = Lazy
    muffin_flour["Maker"] = Maker
    muffin_flour["noMaker"] = noMaker
    muffin_flour["inject"] = inject
    muffin_flour["Config"] = Config
    muffin_flour["DependsOn"] = DependsOn
    muffin_flour["Import"] = Import
    muffin_flour["service"] = service
    muffin_flour["configuration"] = configuration
    muffin_flour["function"] = function
    muffin_flour["struct"] = struct

_register_to_muffin()
