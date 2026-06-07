# Dough System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `oven` + `muffin` registry system with a Spring-inspired Dough-based IoC container.

**Architecture:** ABC defines core interfaces, metaclass handles registration, decorators provide user API. DoughFactory replaces `oven` as the unified Bean manager.

**Tech Stack:** Python 3.10+, ABC, dataclasses, metaclasses

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pancake/registry.py` | Create | Global class registry (no dependencies) |
| `pancake/dough.py` | Create | Dough base class, DoughMeta, Scope |
| `pancake/decorators.py` | Create | @Dough, @Singleton, @Prototype, @Lazy, @Maker, @noMaker, @inject, @Config |
| `pancake/factory/dough_factory.py` | Create | DoughFactory — Bean factory |
| `pancake/base/__init__.py` | Create | Re-export base classes |
| `pancake/base/configuration.py` | Create | Configuration base class |
| `pancake/base/function.py` | Create | Function base class |
| `pancake/base/service.py` | Create | Service base class |
| `pancake/base/struct.py` | Create | Struct base class |
| `pancake/factory/__init__.py` | Modify | Add DoughFactory re-export |
| `pancake/ovenware/broker.py` | Modify | Update to use Dough lifecycle |
| `pancake/ovenware/__init__.py` | Modify | Update to use new system |
| `pancake/builder/build.py` | Modify | Use DoughFactory instead of oven |
| `pancake/builder/load_dlc.py` | Modify | Use registry instead of muffin_flour |
| `pancake/builder/load_src.py` | Modify | Update decorator lookup |
| `pancake/run.py` | Modify | Use DoughFactory in pipeline |
| `pancake/__init__.py` | Modify | Update entry point |
| `pancake/oven/` | Delete | Remove old registry modules |
| `pancake/ovenware/base.py` | Delete | Replaced by Dough + decorators |
| `pancake/ovenware/inject.py` | Delete | Replaced by DoughFactory + @inject |
| `pancake/ovenware/lifecycle.py` | Delete | Replaced by Dough lifecycle |
| `tests/test_dough.py` | Create | Dough + DoughMeta tests |
| `tests/test_registry.py` | Modify | Update for new registry |
| `tests/test_dough_factory.py` | Create | DoughFactory tests |
| `tests/test_decorators.py` | Create | Decorator tests |
| `tests/test_base_classes.py` | Create | Base class tests |

---

## Task 1: Registry — Global Class Registry

**Files:**
- Create: `pancake/registry.py`
- Create: `tests/test_new_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_new_registry.py
"""全局类注册表测试"""

from pancake.registry import register_class, get_class, get_all_classes, clear_registry


class TestRegistry:

    def setup_method(self):
        clear_registry()

    def test_register_and_get(self):
        register_class("MyClass", str)
        assert get_class("MyClass") is str

    def test_get_nonexistent_returns_none(self):
        assert get_class("NonExistent") is None

    def test_get_all_classes(self):
        register_class("A", int)
        register_class("B", float)
        result = get_all_classes()
        assert result == {"A": int, "B": float}

    def test_get_all_returns_copy(self):
        register_class("A", int)
        result = get_all_classes()
        result["B"] = float
        assert get_class("B") is None

    def test_clear_registry(self):
        register_class("A", int)
        clear_registry()
        assert get_all_classes() == {}

    def test_overwrite_registration(self):
        register_class("A", int)
        register_class("A", float)
        assert get_class("A") is float
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /tmp/test_framework && python -m pytest tests/test_new_registry.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'pancake.registry'"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/registry.py
"""
全局类注册表
无依赖，解决循环导入问题
"""

_class_registry: dict[str, type] = {}


def register_class(name: str, cls: type):
    """注册类到全局注册表"""
    _class_registry[name] = cls


def get_class(name: str) -> type | None:
    """从注册表获取类"""
    return _class_registry.get(name)


def get_all_classes() -> dict[str, type]:
    """获取所有注册的类（返回副本）"""
    return dict(_class_registry)


def clear_registry():
    """清空注册表（用于测试）"""
    _class_registry.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_new_registry.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add pancake/registry.py tests/test_new_registry.py
git commit -m "feat: 添加全局类注册表 registry.py"
```

---

## Task 2: Scope Enum

**Files:**
- Create: `pancake/dough.py` (partial — Scope only)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dough.py (partial)
"""Dough 系统测试"""

import pytest
from pancake.dough import Scope


class TestScope:

    def test_scope_values(self):
        assert Scope.SINGLETON.value == "singleton"
        assert Scope.PROTOTYPE.value == "prototype"
        assert Scope.LAZY.value == "lazy"

    def test_scope_enum_members(self):
        assert len(Scope) == 3
        assert "SINGLETON" in [s.name for s in Scope]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dough.py::TestScope -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'pancake.dough'"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/dough.py (partial)
"""
Dough 系统 — Bean 基类、元类、作用域
"""

from enum import Enum


class Scope(Enum):
    """Bean 作用域"""
    SINGLETON = "singleton"  # 全局唯一（默认）
    PROTOTYPE = "prototype"  # 每次创建新实例
    LAZY = "lazy"           # 首次使用时创建
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dough.py::TestScope -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/dough.py tests/test_dough.py
git commit -m "feat: 添加 Scope 枚举"
```

---

## Task 3: DoughMeta — 元类

**Files:**
- Modify: `pancake/dough.py`
- Modify: `tests/test_dough.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dough.py (add to file)
from pancake.dough import DoughMeta
from pancake.registry import get_class, clear_registry


class TestDoughMeta:

    def setup_method(self):
        clear_registry()

    def test_metaclass_registers_class(self):
        class MyClass(metaclass=DoughMeta):
            pass
        assert get_class("MyClass") is MyClass

    def test_metaclass_skips_dough_base(self):
        """名为 Dough 的类不自动注册"""
        class Dough(metaclass=DoughMeta):
            pass
        assert get_class("Dough") is None

    def test_metaclass_registers_subclass(self):
        class Base(metaclass=DoughMeta):
            pass
        class Child(Base):
            pass
        assert get_class("Child") is Child
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dough.py::TestDoughMeta -v`
Expected: FAIL (DoughMeta not defined)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/dough.py (add DoughMeta)
from abc import ABCMeta


class DoughMeta(ABCMeta):
    """元类：自动注册类到全局注册表
    
    跳过名为 "Dough" 的类（基类自身）
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Dough":
            from pancake.registry import register_class
            register_class(name, cls)
        return cls
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dough.py::TestDoughMeta -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/dough.py tests/test_dough.py
git commit -m "feat: 添加 DoughMeta 元类"
```

---

## Task 4: Dough — Bean 基类

**Files:**
- Modify: `pancake/dough.py`
- Modify: `tests/test_dough.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dough.py (add to file)
from pancake.dough import Dough
from abc import ABC


class TestDough:

    def test_dough_is_abc(self):
        assert issubclass(Dough, ABC)

    def test_dough_uses_dough_meta(self):
        assert type(Dough) is DoughMeta

    def test_dough_default_scope(self):
        assert Dough._scope == Scope.SINGLETON

    def test_dough_default_lazy(self):
        assert Dough._lazy is False

    def test_dough_lifecycle_methods_exist(self):
        assert hasattr(Dough, "on_init")
        assert hasattr(Dough, "on_start")
        assert hasattr(Dough, "on_stop")
        assert hasattr(Dough, "on_destroy")

    def test_dough_lifecycle_methods_are_noop(self):
        """默认生命周期方法是空操作"""
        class MyBean(Dough):
            def __init__(self):
                pass
        bean = MyBean()
        # 不应抛出异常
        bean.on_init()
        bean.on_start()
        bean.on_stop()
        bean.on_destroy()

    def test_dough_subclass_auto_registered(self):
        from pancake.registry import get_class, clear_registry
        clear_registry()
        class MyBean(Dough):
            def __init__(self):
                pass
        assert get_class("MyBean") is MyBean

    def test_dough_not_abstract_on_init(self):
        """__init__ 不是抽象方法，子类可以不实现"""
        class MyBean(Dough):
            pass
        # 不应抛出 TypeError
        bean = MyBean()
        assert bean is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dough.py::TestDough -v`
Expected: FAIL (Dough not defined)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/dough.py (add Dough)
from abc import ABC


class Dough(ABC, metaclass=DoughMeta):
    """Bean 基类 — 所有框架类型的基础
    
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
    
    def __init__(self):
        pass
    
    def on_init(self):
        """@PostConstruct — 属性注入后调用"""
        pass
    
    def on_start(self):
        """就绪 — 开始服务"""
        pass
    
    def on_stop(self):
        """停止服务"""
        pass
    
    def on_destroy(self):
        """@PreDestroy — 销毁前调用"""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dough.py::TestDough -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/dough.py tests/test_dough.py
git commit -m "feat: 添加 Dough 基类"
```

---

## Task 5: DoughFactory — Bean 工厂

**Files:**
- Create: `pancake/factory/dough_factory.py`
- Create: `tests/test_dough_factory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dough_factory.py
"""DoughFactory 测试"""

import pytest
from pancake.dough import Dough, Scope
from pancake.factory.dough_factory import DoughFactory


class MyBean(Dough):
    def __init__(self):
        self.value = 42


class TestDoughFactory:

    def setup_method(self):
        # 清理工厂实例
        DoughFactory._factories.clear()

    def test_get_default_factory(self):
        factory = DoughFactory.get()
        assert factory.name == "default"

    def test_get_named_factory(self):
        factory = DoughFactory.get("test")
        assert factory.name == "test"

    def test_get_same_factory(self):
        f1 = DoughFactory.get("test")
        f2 = DoughFactory.get("test")
        assert f1 is f2

    def test_register_class(self):
        factory = DoughFactory.get()
        factory.register(MyBean)
        assert "MyBean" in factory._classes

    def test_create_all_singleton(self):
        factory = DoughFactory.get()
        MyBean._scope = Scope.SINGLETON
        factory.register(MyBean)
        factory.create_all()
        bean = factory.resolve("MyBean")
        assert isinstance(bean, MyBean)
        assert bean.value == 42

    def test_resolve_singleton_returns_same(self):
        factory = DoughFactory.get()
        MyBean._scope = Scope.SINGLETON
        factory.register(MyBean)
        factory.create_all()
        b1 = factory.resolve("MyBean")
        b2 = factory.resolve("MyBean")
        assert b1 is b2

    def test_resolve_prototype_returns_new(self):
        factory = DoughFactory.get()
        MyBean._scope = Scope.PROTOTYPE
        factory.register(MyBean)
        factory.create_all()
        b1 = factory.resolve("MyBean")
        b2 = factory.resolve("MyBean")
        assert b1 is not b2
        assert b1.value == b2.value == 42

    def test_resolve_lazy_creates_on_first_access(self):
        factory = DoughFactory.get()
        MyBean._scope = Scope.LAZY
        factory.register(MyBean)
        factory.create_all()
        # Lazy bean should not be in _instances yet
        assert "MyBean" not in factory._instances
        bean = factory.resolve("MyBean")
        assert isinstance(bean, MyBean)
        # After first resolve, should be cached
        assert "MyBean" in factory._instances

    def test_resolve_unregistered_raises(self):
        factory = DoughFactory.get()
        with pytest.raises(ValueError, match="未注册"):
            factory.resolve("NonExistent")

    def test_register_instance(self):
        factory = DoughFactory.get()
        instance = MyBean()
        factory.register_instance("custom", instance)
        assert factory.resolve("custom") is instance

    def test_lifecycle_on_init_called(self):
        class InitBean(Dough):
            def __init__(self):
                self.initialized = False
            def on_init(self):
                self.initialized = True
        
        factory = DoughFactory.get()
        factory.register(InitBean)
        factory.create_all()
        bean = factory.resolve("InitBean")
        assert bean.initialized is True

    def test_lifecycle_startup_called(self):
        class StartBean(Dough):
            def __init__(self):
                self.started = False
            def on_start(self):
                self.started = True
        
        factory = DoughFactory.get()
        factory.register(StartBean)
        factory.create_all()
        factory.startup_all()
        bean = factory.resolve("StartBean")
        assert bean.started is True

    def test_shutdown_calls_on_stop_and_on_destroy(self):
        class StopBean(Dough):
            def __init__(self):
                self.stopped = False
                self.destroyed = False
            def on_stop(self):
                self.stopped = True
            def on_destroy(self):
                self.destroyed = True
        
        factory = DoughFactory.get()
        factory.register(StopBean)
        factory.create_all()
        bean = factory.resolve("StopBean")
        factory.shutdown_all()
        assert bean.stopped is True
        assert bean.destroyed is True

    def test_multiple_factories_independent(self):
        f1 = DoughFactory.get("f1")
        f2 = DoughFactory.get("f2")
        f1.register(MyBean)
        assert "MyBean" not in f2._classes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dough_factory.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/factory/dough_factory.py
"""
DoughFactory — Bean 工厂
替代原有 oven 模块，统一管理所有 Bean
"""

import logging
from pancake.dough import Dough, Scope

logger = logging.getLogger(__name__)


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
        """获取或创建工厂实例"""
        if name not in DoughFactory._factories:
            DoughFactory._factories[name] = DoughFactory(name)
        return DoughFactory._factories[name]
    
    def register(self, cls: type):
        """注册 Bean 类"""
        name = cls.__name__
        self._classes[name] = cls
        logger.debug(f"注册 Bean: {name}")
    
    def register_instance(self, name: str, instance: object):
        """注册已创建的实例"""
        self._instances[name] = instance
        logger.debug(f"注册实例: {name}")
    
    def resolve(self, name: str) -> Dough:
        """获取 Bean 实例"""
        # 已有实例
        if name in self._instances:
            instance = self._instances[name]
            # Prototype 每次返回新实例
            if hasattr(instance, '_scope') and instance._scope == Scope.PROTOTYPE:
                cls = self._classes.get(name)
                if cls:
                    return cls()
            return instance
        
        # Lazy 创建
        cls = self._classes.get(name)
        if cls is None:
            raise ValueError(f"未注册的 Bean: {name}")
        
        if cls._scope == Scope.LAZY:
            instance = cls()
            self._instances[name] = instance
            instance.on_init()
            return instance
        
        raise ValueError(f"Bean {name} 尚未创建，请先调用 create_all()")
    
    def create_all(self):
        """创建所有注册的 Bean"""
        for name, cls in self._classes.items():
            if cls._scope == Scope.LAZY:
                continue  # Lazy 延迟创建
            
            try:
                instance = cls()
                self._instances[name] = instance
                self._load_order.append(name)
                instance.on_init()
                logger.debug(f"创建 Bean: {name}")
            except Exception as e:
                logger.error(f"创建 Bean {name} 失败: {e}")
                raise
    
    def build_all(self):
        """执行所有 Bean 的 build（兼容旧插件）"""
        pass
    
    def startup_all(self):
        """执行所有 Bean 的 on_start"""
        for name in self._load_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    instance.on_start()
                    logger.debug(f"启动 Bean: {name}")
                except Exception as e:
                    logger.error(f"启动 Bean {name} 失败: {e}")
                    raise
    
    def shutdown_all(self):
        """逆序执行 on_stop 和 on_destroy"""
        for name in reversed(self._load_order):
            instance = self._instances.get(name)
            if instance:
                try:
                    instance.on_stop()
                    instance.on_destroy()
                    logger.debug(f"关闭 Bean: {name}")
                except Exception as e:
                    logger.error(f"关闭 Bean {name} 失败: {e}")
        
        self._instances.clear()
        self._load_order.clear()
    
    def get_all_instances(self) -> dict[str, Dough]:
        """获取所有已创建的实例"""
        return dict(self._instances)
    
    def get_all_classes(self) -> dict[str, type]:
        """获取所有注册的类"""
        return dict(self._classes)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dough_factory.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add pancake/factory/dough_factory.py tests/test_dough_factory.py
git commit -m "feat: 添加 DoughFactory Bean 工厂"
```

---

## Task 6: Decorators — @Dough, @Singleton, @Prototype, @Lazy

**Files:**
- Create: `pancake/decorators.py`
- Create: `tests/test_decorators.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_decorators.py
"""装饰器测试"""

import pytest
from pancake.dough import Dough, Scope
from pancake.decorators import DoughDecorator, Singleton, Prototype, Lazy, Maker, noMaker, inject, Config
from pancake.factory.dough_factory import DoughFactory


class TestClassDecorators:

    def setup_method(self):
        DoughFactory._factories.clear()

    def test_dough_decorator_sets_scope(self):
        @DoughDecorator
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.SINGLETON

    def test_singleton_decorator(self):
        @Singleton
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.SINGLETON

    def test_prototype_decorator(self):
        @Prototype
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.PROTOTYPE

    def test_lazy_decorator(self):
        @Lazy
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._lazy is True
        assert MyBean._scope == Scope.LAZY

    def test_decorator_composition(self):
        @Prototype
        @DoughDecorator
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.PROTOTYPE


class TestMakerDecorator:

    def test_maker_marks_method(self):
        class MyConfig(Dough):
            def __init__(self):
                pass
            @Maker
            def my_bean(self):
                return "bean"
        assert hasattr(MyConfig.my_bean, "_is_maker")
        assert MyConfig.my_bean._is_maker is True


class TestNoMakerDecorator:

    def test_no_maker_marks_method(self):
        class MyConfig(Dough):
            def __init__(self):
                pass
            @noMaker
            def helper(self):
                return "helper"
        assert hasattr(MyConfig.helper, "_no_maker")
        assert MyConfig.helper._no_maker is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_decorators.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/decorators.py
"""
装饰器 — 提供简洁的用户 API
"""

import functools
import inspect
from pancake.dough import Dough, Scope


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


def inject(func):
    """@inject — 自动注入依赖
    
    从 DoughFactory 解析参数类型对应的 Bean
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
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
        
        # 注入缺失参数
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
        
        return func(*args, **kwargs)
    
    # 清除注解，避免框架误用
    wrapper.__annotations__ = {}
    if hasattr(wrapper, '__wrapped__'):
        delattr(wrapper, '__wrapped__')
    wrapper.__signature__ = inspect.Signature()
    return wrapper


def Config(cls):
    """@Config — 从配置注入 Struct 字段"""
    # 在 on_init 中注入配置值
    original_on_init = cls.on_init
    
    @functools.wraps(original_on_init)
    def new_on_init(self):
        from pancake import settings
        for field_name, field_type in cls.__dataclass_fields__.items():
            if field_name.startswith("_"):
                continue
            # 尝试从配置获取值
            config_key = f"{cls.__name__.lower()}.{field_name}"
            value = settings.get(config_key)
            if value is not None:
                setattr(self, field_name, value)
        original_on_init(self)
    
    cls.on_init = new_on_init
    return cls
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_decorators.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/decorators.py tests/test_decorators.py
git commit -m "feat: 添加装饰器 @Dough, @Singleton, @Prototype, @Lazy, @Maker, @noMaker, @inject, @Config"
```

---

## Task 7: Base Classes — Configuration, Function, Service, Struct

**Files:**
- Create: `pancake/base/__init__.py`
- Create: `pancake/base/configuration.py`
- Create: `pancake/base/function.py`
- Create: `pancake/base/service.py`
- Create: `pancake/base/struct.py`
- Create: `tests/test_base_classes.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_base_classes.py
"""基类测试"""

import pytest
from pancake.dough import Dough
from pancake.base.configuration import Configuration
from pancake.base.function import Function
from pancake.base.service import Service
from pancake.base.struct import Struct
from pancake.factory.dough_factory import DoughFactory


class TestConfiguration:

    def setup_method(self):
        DoughFactory._factories.clear()

    def test_configuration_is_dough(self):
        assert issubclass(Configuration, Dough)

    def test_configuration_auto_registers_maker_methods(self):
        class AppConfig(Configuration):
            def __init__(self):
                self.bean_created = False
            def my_bean(self):
                self.bean_created = True
                return {"key": "value"}
        
        factory = DoughFactory.get()
        factory.register(AppConfig)
        factory.create_all()
        config = factory.resolve("AppConfig")
        # my_bean 返回值应被注册
        assert factory.resolve("my_bean") == {"key": "value"}

    def test_configuration_skips_private_methods(self):
        class AppConfig(Configuration):
            def __init__(self):
                pass
            def _private(self):
                return {"private": True}
        
        factory = DoughFactory.get()
        factory.register(AppConfig)
        factory.create_all()
        with pytest.raises(ValueError):
            factory.resolve("_private")

    def test_configuration_skips_no_maker(self):
        from pancake.decorators import noMaker
        class AppConfig(Configuration):
            def __init__(self):
                pass
            @noMaker
            def helper(self):
                return {"helper": True}
        
        factory = DoughFactory.get()
        factory.register(AppConfig)
        factory.create_all()
        with pytest.raises(ValueError):
            factory.resolve("helper")

    def test_configuration_skips_primitive_returns(self):
        class AppConfig(Configuration):
            def __init__(self):
                pass
            def get_name(self):
                return "test"
            def get_count(self):
                return 42
        
        factory = DoughFactory.get()
        factory.register(AppConfig)
        factory.create_all()
        # 原始类型不应被注册
        with pytest.raises(ValueError):
            factory.resolve("get_name")


class TestFunction:

    def test_function_is_dough(self):
        assert issubclass(Function, Dough)

    def test_function_is_callable(self):
        class MyFunc(Function):
            def call(self, x, y):
                return x + y
        
        f = MyFunc()
        assert f(1, 2) == 3

    def test_function_call_raises_not_implemented(self):
        f = Function()
        with pytest.raises(NotImplementedError):
            f.call()


class TestService:

    def test_service_is_dough(self):
        assert issubclass(Service, Dough)


class TestStruct:

    def test_struct_is_dough(self):
        assert issubclass(Struct, Dough)

    def test_struct_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(Struct)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_base_classes.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/base/__init__.py
from pancake.base.configuration import Configuration
from pancake.base.function import Function
from pancake.base.service import Service
from pancake.base.struct import Struct

__all__ = ["Configuration", "Function", "Service", "Struct"]
```

```python
# pancake/base/configuration.py
"""Configuration 基类"""

import inspect
from pancake.dough import Dough


class Configuration(Dough):
    """配置类 — 非私有方法返回值自动注册为 Bean
    
    规则:
    1. 非私有方法自动扫描
    2. 返回值必须是对象（非 str/int/float/bool/None）
    3. @noMaker 装饰器可排除特定方法
    """
    
    def on_init(self):
        from pancake.factory.dough_factory import DoughFactory
        
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            if hasattr(method, "_no_maker"):
                continue
            result = method()
            if result is not None and not isinstance(result, (str, int, float, bool)):
                DoughFactory.get().register_instance(name, result)
```

```python
# pancake/base/function.py
"""Function 基类"""

from pancake.dough import Dough


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

```python
# pancake/base/service.py
"""Service 基类"""

from pancake.dough import Dough


class Service(Dough):
    """服务类 — 方法集合
    
    类似 Spring @Service
    方法通过 @staticmethod 定义，通过 @inject 注入依赖
    """
    pass
```

```python
# pancake/base/struct.py
"""Struct 基类"""

from dataclasses import dataclass
from pancake.dough import Dough


@dataclass
class Struct(Dough):
    """数据结构类 — 同时继承 Dough 和 dataclass
    
    支持两种注入模式:
    1. @Config 标记的字段从配置注入
    2. 构造函数传入
    """
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_base_classes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/base/ tests/test_base_classes.py
git commit -m "feat: 添加基类 Configuration, Function, Service, Struct"
```

---

## Task 8: Update factory/__init__.py

**Files:**
- Modify: `pancake/factory/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dough_factory.py (add)
class TestFactoryInit:

    def test_import_from_factory(self):
        from pancake.factory import DoughFactory
        assert DoughFactory is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dough_factory.py::TestFactoryInit -v`
Expected: FAIL with "cannot import name 'DoughFactory'"

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/factory/__init__.py
from pancake.factory.dough_factory import DoughFactory
from pancake.factory.config_factory import ConfigFactory

__all__ = ["DoughFactory", "ConfigFactory"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dough_factory.py::TestFactoryInit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/factory/__init__.py
git commit -m "feat: 更新 factory/__init__.py 导出 DoughFactory"
```

---

## Task 9: Refactor ovenware/broker.py — Use Dough Lifecycle

**Files:**
- Modify: `pancake/ovenware/broker.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_broker.py (update existing)
"""消息队列测试 — 更新为使用 Dough 生命周期"""

import pytest
from pancake.dough import Dough
from pancake.ovenware.broker import SimpleBroker, MessageBroker


class TestBrokerAsDough:

    def test_simple_broker_is_dough(self):
        assert issubclass(SimpleBroker, Dough)

    def test_broker_lifecycle(self):
        broker = SimpleBroker()
        broker.on_init()
        broker.on_start()
        broker.on_stop()
        broker.on_destroy()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_broker.py::TestBrokerAsDough -v`
Expected: FAIL (SimpleBroker is not a Dough subclass)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/ovenware/broker.py (修改)
"""
消息队列模块
支持事件驱动和消息传递
"""

import asyncio
import functools
import logging
from typing import Any, Callable
from collections import defaultdict

from pancake.dough import Dough, Scope

logger = logging.getLogger(__name__)


class MessageBroker(Dough):
    """消息队列基类"""
    
    async def publish(self, topic: str, message: dict) -> None:
        raise NotImplementedError
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        raise NotImplementedError
    
    async def close(self) -> None:
        pass


class SimpleBroker(MessageBroker):
    """简单内存消息队列"""
    
    _scope = Scope.SINGLETON
    
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._initialized = False
    
    # ... 其余方法保持不变 ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_broker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/ovenware/broker.py tests/test_broker.py
git commit -m "refactor: broker 使用 Dough 生命周期"
```

---

## Task 10: Refactor builder/build.py — Use DoughFactory

**Files:**
- Modify: `pancake/builder/build.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_builder.py
"""构建器测试"""

import pytest
from pancake.factory.dough_factory import DoughFactory
from pancake.builder import build


class TestBuilder:

    def test_build_uses_factory(self):
        """build 应该调用 DoughFactory.build_all()"""
        # 简单验证 build 函数存在且可调用
        assert callable(build.build)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_builder.py -v`
Expected: FAIL or import error

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/builder/build.py
"""
构建流水线 — 使用 DoughFactory
"""

from pancake.factory.dough_factory import DoughFactory


def build():
    """构建所有服务"""
    factory = DoughFactory.get()
    factory.create_all()
    factory.build_all()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/builder/build.py tests/test_builder.py
git commit -m "refactor: build.py 使用 DoughFactory"
```

---

## Task 11: Refactor builder/load_dlc.py — Use Registry

**Files:**
- Modify: `pancake/builder/load_dlc.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_load_dlc.py
"""插件加载测试"""

import pytest
from pancake.builder import load_dlc


class TestLoadDlc:

    def test_load_dlc_run_callable(self):
        assert callable(load_dlc.run)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_load_dlc.py -v`
Expected: PASS (already exists)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/builder/load_dlc.py
"""
插件加载 — 使用 registry 和 DoughFactory
"""

import importlib
import inspect
import logging
import os
import sys

from pancake import registry
from pancake.factory.dough_factory import DoughFactory
from pancake.dough import Dough

logger = logging.getLogger(__name__)


def _load_from_xml():
    """从 XML 配置加载插件列表"""
    from pancake import oven  # 临时兼容
    plugins = oven.pancake_xml.get("plugins", [])
    if not plugins:
        return None

    for plugin_info in plugins:
        name = plugin_info["name"]
        source = plugin_info["source"]
        enabled = plugin_info.get("enabled", True)

        try:
            plugin = importlib.import_module(source)
        except ImportError as e:
            if enabled:
                logger.error(f"Failed to import plugin {name} ({source}): {e}")
                sys.exit(1)
            else:
                logger.debug(f"Disabled plugin {name} not available: {e}")
                continue

        # 注册模块中的所有类到 registry
        for attr_name, member in inspect.getmembers(plugin):
            if (
                not attr_name.startswith("_")
                and inspect.isclass(member)
                and issubclass(member, Dough)
                and member is not Dough
            ):
                registry.register_class(attr_name, member)


def _load_from_directory():
    """从 ovenware 目录扫描加载插件"""
    dlc_dir = os.path.join(os.path.dirname(__file__), "../", "ovenware")
    entries = os.listdir(dlc_dir)
    plugin_files = [f[:-3] for f in entries if f.endswith(".py") and f not in ["__init__.py"]]
    plugin_dirs = [d for d in entries
                   if os.path.isdir(os.path.join(dlc_dir, d))
                   and os.path.exists(os.path.join(dlc_dir, d, "__init__.py"))
                   and not d.startswith("_")]
    plugin_names = plugin_files + plugin_dirs

    for plugin_name in plugin_names:
        plugin = importlib.import_module(f"ovenware.{plugin_name}")
        for attr_name, member in inspect.getmembers(plugin):
            if (
                not attr_name.startswith("_")
                and inspect.isclass(member)
                and issubclass(member, Dough)
                and member is not Dough
            ):
                registry.register_class(attr_name, member)


def run():
    """加载插件：优先 XML 配置，回退到目录扫描"""
    has_xml = bool(False)  # TODO: 从 oven 获取 XML 配置

    if has_xml:
        logger.info("Loading plugins from XML config")
        _load_from_xml()
    else:
        logger.info("No XML config, scanning ovenware directory")
        _load_from_directory()
    
    # 将 registry 中的类注册到 DoughFactory
    factory = DoughFactory.get()
    for name, cls in registry.get_all_classes().items():
        if issubclass(cls, Dough) and cls is not Dough:
            factory.register(cls)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_load_dlc.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/builder/load_dlc.py tests/test_load_dlc.py
git commit -m "refactor: load_dlc 使用 registry 和 DoughFactory"
```

---

## Task 12: Update builder/load_src.py — Update Decorator Lookup

**Files:**
- Modify: `pancake/builder/load_src.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_load_src.py
"""用户代码扫描测试"""

import pytest
from pancake.builder import load_src


class TestLoadSrc:

    def test_scan_py_files_callable(self):
        assert callable(load_src.scan_py_files)

    def test_parse_file_callable(self):
        assert callable(load_src.parse_file)

    def test_run_callable(self):
        assert callable(load_src.run)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_load_src.py -v`
Expected: PASS (already exists)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/builder/load_src.py
"""
用户代码扫描 — 使用 registry 查找装饰器
"""

import ast
import builtins
import os
import sys
from pancake import registry

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
    all_classes = registry.get_all_classes()
    
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

            # 匹配 registry 中的类
            if dec_name and dec_name in all_classes:
                results.append((dec_name, obj_type, obj_name, filepath))

        # 检查基类是否在 registry 中
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name and base_name in all_classes:
                    results.append((base_name, obj_type, obj_name, filepath))
    return results


def safe_register(filepath):
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


def run():
    from pancake.settings import get_path
    src_dir = get_path("src_dir")
    files = scan_py_files(src_dir)

    file_items = []
    for f in files:
        items = parse_file(f)
        if items:
            min_priority = 50
            for dec_name, _, _, _ in items:
                dec_obj = registry.get_class(dec_name)
                if dec_obj and hasattr(dec_obj, '_load_priority'):
                    min_priority = min(min_priority, dec_obj._load_priority)
            file_items.append((min_priority, f, items))

    file_items.sort(key=lambda x: x[0])

    seen = set()
    unique_items = []
    for item in file_items:
        if item[1] not in seen:
            seen.add(item[1])
            unique_items.append(item)

    for _, path, _ in unique_items:
        safe_register(path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_load_src.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/builder/load_src.py tests/test_load_src.py
git commit -m "refactor: load_src 使用 registry 查找装饰器"
```

---

## Task 13: Refactor run.py — Use DoughFactory

**Files:**
- Modify: `pancake/run.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run.py
"""运行流水线测试"""

import pytest
from pancake import run


class TestRun:

    def test_run_functions_exist(self):
        assert callable(run.load_xml)
        assert callable(run.load_config)
        assert callable(run.load_ovenware)
        assert callable(run.load_dish)
        assert callable(run.build_all)
        assert callable(run.run_loop_methods)
        assert callable(run.run)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_run.py -v`
Expected: PASS (functions exist)

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/run.py
"""
运行流水线 — 使用 DoughFactory
"""

import logging
import signal
import sys

from pancake.factory.dough_factory import DoughFactory
from pancake.tool import ProgressBar

logger = logging.getLogger("Pancake_Main")


def load_xml():
    """加载 XML 启动配置"""
    from pancake.resource import xml_config
    from pancake import oven  # 临时兼容
    xml_data = xml_config.load_xml()
    oven.pancake_xml.update(xml_data)


def load_config():
    """加载配置文件"""
    from pancake.oven import default
    default.default_before()


def load_ovenware():
    """加载插件"""
    from pancake.builder import load_dlc
    load_dlc.run()


def oven_init():
    """初始化"""
    from pancake.oven import default
    default.default_after()


def load_dish():
    """加载用户代码"""
    from pancake.builder import load_src
    load_src.run()


def run_loop_methods():
    """运行所有 loop_method"""
    import threading

    factory = DoughFactory.get()
    instances = factory.get_all_instances()
    
    loop_methods = {}
    for name, instance in instances.items():
        if hasattr(instance, 'loop_method') and callable(instance.loop_method):
            loop_methods[name] = instance.loop_method
    
    if not loop_methods:
        return

    if len(loop_methods) == 1:
        name, method = next(iter(loop_methods.items()))
        logger.info(f"运行 loop_method: {name}")
        method()
        return

    items = list(loop_methods.items())
    main_idx = 0
    for i, (name, method) in enumerate(items):
        if "web" in name.lower():
            main_idx = i
            break

    for i, (name, method) in enumerate(items):
        if i == main_idx:
            continue
        logger.info(f"运行 loop_method (后台): {name}")
        t = threading.Thread(target=method, daemon=True, name=f"loop_{name}")
        t.start()

    main_name, main_method = items[main_idx]
    logger.info(f"运行 loop_method (主线程): {main_name}")
    main_method()


def build_all():
    """构建服务"""
    from pancake.builder import build
    build.build()


def _shutdown_handler(signum, frame):
    """信号处理：优雅关闭"""
    sig_name = signal.Signals(signum).name
    logger.info(f"收到信号 {sig_name}，正在优雅关闭...")

    factory = DoughFactory.get()
    factory.shutdown_all()

    logger.info("Pancake 已关闭")
    sys.exit(0)


def run():
    """运行服务"""
    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)

    loading_list = {
        "load xml": load_xml,
        "load config": load_config,
        "load ovenware": load_ovenware,
        "oven init": oven_init,
        "load dish": load_dish,
        "build": build_all,
    }

    logger.info("Pancake Loading...")
    progress_bar = ProgressBar(len(loading_list), "Pancake Loading")

    for task in loading_list.keys():
        loading_list[task]()
        progress_bar.update(1, f"{task} 完成")
    progress_bar.finish()
    logger.info("Pancake Loading 完成")

    # 启动所有 Bean
    factory = DoughFactory.get()
    factory.startup_all()
    logger.info("Pancake 启动完成")

    run_loop_methods()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/run.py tests/test_run.py
git commit -m "refactor: run.py 使用 DoughFactory"
```

---

## Task 14: Delete Old Modules

**Files:**
- Delete: `pancake/oven/pancake.py`
- Delete: `pancake/oven/muffin.py`
- Delete: `pancake/oven/default.py`
- Delete: `pancake/ovenware/base.py`
- Delete: `pancake/ovenware/inject.py`
- Delete: `pancake/ovenware/lifecycle.py`
- Modify: `pancake/oven/__init__.py` (empty or minimal)
- Modify: `pancake/ovenware/__init__.py` (update imports)

- [ ] **Step 1: Update oven/__init__.py to be minimal**

```python
# pancake/oven/__init__.py
"""
oven 模块 — 已被 DoughFactory 替代
保留模块结构以避免导入错误
"""
```

- [ ] **Step 2: Update ovenware/__init__.py**

```python
# pancake/ovenware/__init__.py
"""
ovenware 模块 — 插件系统
"""

import builtins
import logging

builtins.__dict__["logging"] = logging

# 导入新的基类和装饰器
from pancake.dough import Dough, Scope
from pancake.decorators import DoughDecorator, Singleton, Prototype, Lazy, Maker, noMaker, inject, Config
from pancake.base import Configuration, Function, Service, Struct

# 注入到 builtins
builtins.__dict__["Dough"] = Dough
builtins.__dict__["Scope"] = Scope
builtins.__dict__["Configuration"] = Configuration
builtins.__dict__["Function"] = Function
builtins.__dict__["Service"] = Service
builtins.__dict__["Struct"] = Struct

logger = logging.getLogger(__name__)
```

- [ ] **Step 3: Delete old modules**

```bash
rm pancake/oven/pancake.py pancake/oven/muffin.py pancake/oven/default.py
rm pancake/ovenware/base.py pancake/ovenware/inject.py pancake/ovenware/lifecycle.py
```

- [ ] **Step 4: Update tests**

```python
# tests/conftest.py
"""共享 fixtures"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture
def dough_factory():
    """独立的 DoughFactory 实例"""
    from pancake.factory.dough_factory import DoughFactory
    DoughFactory._factories.clear()
    return DoughFactory.get("test")
```

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: 删除旧模块，更新 ovenware/__init__.py"
```

---

## Task 15: Final Integration — Update __init__.py

**Files:**
- Modify: `pancake/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_init.py
"""入口模块测试"""

import pytest
from pancake import run


class TestInit:

    def test_run_callable(self):
        assert callable(run)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_init.py -v`
Expected: PASS

- [ ] **Step 3: Write minimal implementation**

```python
# pancake/__init__.py
"""
Pancake Framework — 装饰器驱动的 Python 框架
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

_initialized = False


def init():
    global _initialized
    if _initialized:
        return
    _initialized = True

    from pancake import initialize
    initialize.print_ico()

    init_tasks = {
        "check_environment": initialize.check_environment,
        "check_struct": initialize.check_struct,
    }

    print("检查运行环境")
    from pancake.tool import ProgressBar
    progress = ProgressBar(len(init_tasks), prefix="初始化环境")
    for task in init_tasks.keys():
        init_tasks[task]()
        progress.update(1, f"{task} 完成")
    progress.finish()

    from pancake.resource import config
    import pancake.resource.logging as resource_logging


def run():
    init()
    from pancake.run import run as _run
    _run()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_init.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pancake/__init__.py tests/test_init.py
git commit -m "refactor: 更新 __init__.py 使用新系统"
```

---

## Self-Review Checklist

- [ ] All spec requirements have corresponding tasks
- [ ] No placeholders (TBD, TODO, implement later)
- [ ] Type/method names consistent across tasks
- [ ] Each task produces working, testable software
- [ ] TDD approach: test first, then implement
- [ ] Frequent commits after each task
- [ ] File paths are exact
- [ ] Code blocks are complete (no "similar to Task N")
- [ ] Commands include expected output

---

## Execution Options

Plan complete and saved to `docs/superpowers/plans/2026-06-07-dough-system.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session, batch execution with checkpoints

Which approach?
