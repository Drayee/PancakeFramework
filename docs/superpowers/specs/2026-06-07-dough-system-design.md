# Dough System Design Spec

> Pancake Framework v2 — Spring-inspired IoC Container with Dough-based Bean System

## Overview

Replace the current `oven` + `muffin` registry system with a unified **DoughFactory** that manages all Beans through the **Dough** base class hierarchy. Inspired by Spring Framework's IoC container.

## Core Concepts

### Dough — Bean 基类

所有框架类型的基础。使用 ABC 定义核心接口，元类处理注册和生命周期。

```python
from abc import ABC
from enum import Enum

class Scope(Enum):
    SINGLETON = "singleton"  # 全局唯一（默认）
    PROTOTYPE = "prototype"  # 每次创建新实例
    LAZY = "lazy"           # 首次使用时创建

class DoughMeta(type(ABC)):
    """元类：自动注册类到全局注册表"""
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Dough":
            from pancake.registry import register_class
            register_class(name, cls)
        return cls

class Dough(ABC, metaclass=DoughMeta):
    """Bean 基类
    
    生命周期:
        1. __init__()     — 构造
        2. on_init()      — @PostConstruct, 属性注入后
        3. on_start()     — 就绪，开始服务
        4. [使用中]
        5. on_stop()      — 停止服务
        6. on_destroy()   — @PreDestroy, 销毁前
    """
    
    _scope: Scope = Scope.SINGLETON
    _lazy: bool = False
    _name: str = ""
    
    def __init__(self): pass
    def on_init(self): pass
    def on_start(self): pass
    def on_stop(self): pass
    def on_destroy(self): pass
```

### DoughFactory — Bean 工厂

替代原有 `oven` 模块，统一管理所有 Bean。

```python
class DoughFactory:
    """Bean 工厂 — 管理 Bean 的注册、创建、生命周期
    
    支持多个独立工厂实例
    """
    _factories: dict[str, "DoughFactory"] = {}
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._classes: dict[str, type] = {}
        self._instances: dict[str, Dough] = {}
        self._load_order: list[str] = []
        DoughFactory._factories[name] = self
    
    @staticmethod
    def get(name: str = "default") -> "DoughFactory":
        if name not in DoughFactory._factories:
            DoughFactory._factories[name] = DoughFactory(name)
        return DoughFactory._factories[name]
    
    def register(self, cls: type): ...
    def register_instance(self, name: str, instance: object): ...
    def resolve(self, name: str) -> Dough: ...
    def create_all(self): ...
    def build_all(self): ...
    def startup_all(self): ...
    def shutdown_all(self): ...
```

### Registry — 全局类注册表

无依赖的全局注册表，解决循环导入问题。

```python
# pancake/registry.py
_class_registry: dict[str, type] = {}

def register_class(name: str, cls: type):
    _class_registry[name] = cls

def get_class(name: str) -> type:
    return _class_registry.get(name)

def get_all_classes() -> dict[str, type]:
    return dict(_class_registry)
```

## Base Classes

### Configuration — 配置类

```python
class Configuration(Dough):
    """配置类 — 非私有方法返回值自动注册为 Bean
    
    规则:
    1. 非私有方法自动扫描
    2. 返回值必须是对象（非 str/int/float/bool/None）
    3. @noMaker 装饰器可排除特定方法
    """
    def on_init(self):
        import inspect
        from pancake.factory import DoughFactory
        
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            if hasattr(method, "_no_maker"):
                continue
            result = method()
            if result is not None and not isinstance(result, (str, int, float, bool)):
                DoughFactory.get().register_instance(name, result)
```

### Function — 方法类

```python
class Function(Dough):
    """方法类 — 包装函数，提供 call() 方法
    
    使用时直接调用即可:
        my_func = MyFunction()
        result = my_func(args)
    """
    def call(self, *args, **kwargs):
        raise NotImplementedError
    
    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)
```

### Service — 服务类

```python
class Service(Dough):
    """服务类 — 方法集合
    
    类似 Spring @Service
    方法通过 @staticmethod 定义，通过 @inject 注入依赖
    """
    pass
```

### Struct — 数据结构类

```python
from dataclasses import dataclass

@dataclass
class Struct(Dough):
    """数据结构类 — 同时继承 Dough 和 dataclass
    
    支持两种注入模式:
    1. @Config 标记的字段从配置注入
    2. 构造函数传入
    """
    pass
```

## Decorators

### 类装饰器

```python
@Dough          # 标记类为 Bean（等同于 Spring @Component）
@Singleton      # 单例作用域（默认）
@Prototype      # 每次获取创建新实例
@Lazy           # 延迟初始化，首次使用时创建
```

### 方法装饰器

```python
@Maker          # 标记方法返回值为 Bean（等同于 Spring @Bean）
@noMaker        # 排除方法，不自动注册
@inject         # 自动注入依赖
@Config         # 从配置注入字段值
```

### 装饰器组合

```python
@Singleton
@Dough
class MyBean(Dough): ...

# 等价于
@Dough(scope=Scope.SINGLETON)
class MyBean(Dough): ...
```

## File Structure

```
pancake/
├── __init__.py          # 入口: init() → run()
├── run.py               # 启动流水线（重构）
├── cli.py               # CLI（保留）
├── settings.py          # 配置管理（保留）
├── dough.py             # Dough 基类 + DoughMeta + Scope
├── registry.py          # 全局类注册表（无依赖）
├── decorators.py        # 所有装饰器
├── factory/
│   ├── __init__.py
│   ├── dough_factory.py # DoughFactory
│   └── config_factory.py # ConfigFactory（保留）
├── base/
│   ├── __init__.py
│   ├── configuration.py # Configuration
│   ├── function.py      # Function
│   ├── service.py       # Service
│   └── struct.py        # Struct
├── ovenware/
│   ├── __init__.py      # 插件加载（重构）
│   ├── broker.py        # 消息队列（保留）
│   └── embed.py         # builtins 注入（重构）
├── builder/
│   ├── __init__.py
│   ├── build.py         # 构建流水线（重构）
│   ├── load_dlc.py      # 插件加载（重构）
│   └── load_src.py      # 用户代码扫描（保留，更新逻辑）
├── resource/            # 配置加载（保留）
├── tool/                # 工具（保留）
└── initialize/          # 环境检查（保留）
```

## Data Flow

```
main.py → pancake.run()
  → init()                    # 环境检查
  → load_xml()                # 加载 pancake.xml
  → load_config()             # 加载 YAML/JSON 配置
  → DoughFactory.create_all() # 创建所有 Bean（按 init_order）
    → 对每个 Bean:
      1. __init__()
      2. 属性注入（@Config 字段）
      3. on_init()  (@PostConstruct)
  → DoughFactory.build_all()  # 执行 build
  → load_dish()               # 扫描用户代码
  → DoughFactory.startup_all() # 执行 on_start
  → run_loop_methods()        # 运行 loop_method
```

## Bean Resolution

```python
# 获取 Bean 实例
bean = DoughFactory.get().resolve("my_bean")

# 自动注入
@inject
def my_func(service: MyService):
    # MyService 自动从 DoughFactory 获取
    ...
```

## Scope Behavior

| Scope | 创建时机 | 实例数量 | 销毁时机 |
|-------|---------|---------|---------|
| Singleton | 启动时 | 1 | 关闭时 |
| Prototype | 每次 resolve | N | GC 回收 |
| Lazy | 首次 resolve | 1 | 关闭时 |

## Migration from Current System

| Current | New |
|---------|-----|
| `oven.pancake_yaml` | `ConfigFactory.get().get_all()` |
| `oven.pancake_dough` | `DoughFactory.get()._classes` |
| `oven.pancake_pie` | `DoughFactory.get()._instances` |
| `oven.muffin_flour` | `registry._class_registry` |
| `oven.muffin_egg` | `DoughFactory.get()._load_order` |
| `@Service` decorator | `@Dough` + `class MyService(Service): ...` |
| `@Mapper` decorator | Plugin-provided, inherits Dough |
| `InitAction` base class | `Dough` base class |
| `Lifecycle` base class | `Dough` lifecycle methods |
| `IoCContainer` | `DoughFactory` |
| `auto_inject` | `@inject` decorator |
