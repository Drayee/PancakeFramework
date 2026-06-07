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
