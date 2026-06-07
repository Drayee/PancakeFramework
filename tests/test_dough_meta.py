"""测试 DoughMeta 自动注册改进

- _no_register = True 跳过注册
- 类名冲突警告
"""

import os
import sys
import warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pancake.registry import clear_registry, get_class
from pancake.dough import Dough, DoughMeta


def setup():
    """每个测试前清空注册表"""
    clear_registry()


def test_no_register_flag():
    """_no_register = True 的类不注册到注册表"""
    setup()

    class TempClass(Dough):
        _no_register = True

    assert get_class("TempClass") is None
    print("[OK] _no_register = True 跳过注册")


def test_normal_class_registered():
    """正常类仍然自动注册"""
    setup()

    class NormalClass(Dough):
        pass

    assert get_class("NormalClass") is NormalClass
    print("[OK] 正常类自动注册")


def test_class_name_collision_warning():
    """类名冲突时发出警告"""
    setup()

    class MyClass(Dough):
        pass

    assert get_class("MyClass") is MyClass

    # 同名类应该触发警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class MyClass(Dough):  # noqa: F811
            pass

        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "类名冲突" in str(w[0].message)
        assert "MyClass" in str(w[0].message)
        print("[OK] 类名冲突触发警告")


def test_no_warning_for_same_class():
    """同一个类重复创建不触发警告"""
    setup()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class SingleClass(Dough):
            pass

        # 仅定义一次，不应有警告
        assert len(w) == 0
        print("[OK] 单次定义不触发警告")


def test_mock_class_skip_register():
    """测试中的 mock 类可以用 _no_register 跳过"""
    setup()

    class MockService(Dough):
        _no_register = True
        pass

    class RealService(Dough):
        pass

    assert get_class("MockService") is None
    assert get_class("RealService") is RealService
    print("[OK] Mock 类跳过注册，正常类正常注册")


if __name__ == "__main__":
    test_no_register_flag()
    test_normal_class_registered()
    test_class_name_collision_warning()
    test_no_warning_for_same_class()
    test_mock_class_skip_register()
    print("\n所有测试通过！")
