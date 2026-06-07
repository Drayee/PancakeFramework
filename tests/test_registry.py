"""注册表测试 — 统一注册表"""

import pytest
from pancake.registry import (
    register_class, get_class, get_all_classes, clear_registry,
    register_decorator, get_decorator, get_all_decorators,
    register_instance, get_instance, get_all_instances,
    set_runtime, get_runtime,
    flour, water, egg, sugar,
)


@pytest.fixture
def clean():
    """每个测试前清空注册表"""
    clear_registry()
    yield
    clear_registry()


class TestClassRegistry:

    def test_register_and_get(self, clean):
        register_class("MyClass", str)
        assert get_class("MyClass") is str

    def test_get_nonexistent(self, clean):
        assert get_class("Nonexistent") is None

    def test_get_all(self, clean):
        register_class("A", int)
        register_class("B", float)
        classes = get_all_classes()
        assert "A" in classes
        assert "B" in classes

    def test_overwrite(self, clean):
        register_class("X", int)
        register_class("X", float)
        assert get_class("X") is float


class TestDecoratorRegistry:

    def test_register_and_get(self, clean):
        register_decorator("my_dec", lambda: None)
        assert get_decorator("my_dec") is not None

    def test_has_decorator(self, clean):
        register_decorator("exists", lambda: None)
        assert has_decorator("exists")
        assert not has_decorator("not_exists")


class TestInstanceRegistry:

    def test_register_and_get(self, clean):
        obj = object()
        register_instance("my_obj", obj)
        assert get_instance("my_obj") is obj

    def test_get_nonexistent(self, clean):
        assert get_instance("nonexistent") is None

    def test_get_all(self, clean):
        register_instance("a", 1)
        register_instance("b", 2)
        instances = get_all_instances()
        assert instances["a"] == 1
        assert instances["b"] == 2


class TestRuntimeRegistry:

    def test_set_and_get(self, clean):
        set_runtime("key", "value")
        assert get_runtime("key") == "value"

    def test_default(self, clean):
        assert get_runtime("missing", "default") == "default"


class TestFlourWater:
    """测试 flour/water (原 muffin) 注册表"""

    def test_flour_is_dict(self):
        assert isinstance(flour, dict)

    def test_water_is_dict(self):
        assert isinstance(water, dict)

    def test_flour_contains_decorators(self):
        """flour 应包含框架装饰器"""
        assert "inject" in flour
        assert "Singleton" in flour

    def test_water_contains_classes(self):
        """water 应包含框架类"""
        assert "DoughFactory" in water
        assert "Service" in water


def has_decorator(name: str) -> bool:
    from pancake.registry import has_decorator as _has
    return _has(name)
