"""Decorators 测试"""

import pytest
from pancake.dough import Dough
from pancake.decorators import DependsOn, Import


class TestDependsOn:

    def test_depends_on_sets_attribute(self):
        @DependsOn("ServiceA", "ServiceB")
        class MyService(Dough):
            def __init__(self):
                pass

        assert MyService._depends_on == ["ServiceA", "ServiceB"]

    def test_depends_on_empty(self):
        @DependsOn()
        class EmptyDeps(Dough):
            def __init__(self):
                pass

        assert EmptyDeps._depends_on == []

    def test_depends_on_preserves_class(self):
        """装饰器不改变类本身"""
        @DependsOn("X")
        class Original(Dough):
            def __init__(self):
                self.marker = 123

        assert Original().marker == 123
        assert Original.__name__ == "Original"


class TestImport:

    def test_import_sets_attribute(self):
        class External(Dough):
            def __init__(self):
                pass

        @Import(External)
        class Config(Dough):
            def __init__(self):
                pass

        assert Config._imports == [External]

    def test_import_multiple_classes(self):
        class A(Dough):
            def __init__(self):
                pass

        class B(Dough):
            def __init__(self):
                pass

        @Import(A, B)
        class Config(Dough):
            def __init__(self):
                pass

        assert Config._imports == [A, B]

    def test_import_preserves_class(self):
        """装饰器不改变类本身"""
        class External(Dough):
            def __init__(self):
                pass

        @Import(External)
        class Config(Dough):
            def __init__(self):
                self.val = 42

        assert Config().val == 42
        assert Config.__name__ == "Config"
