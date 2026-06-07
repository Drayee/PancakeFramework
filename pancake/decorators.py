"""
Decorators — 框架装饰器
提供 @DependsOn、@Import 等声明式装饰器
"""


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
