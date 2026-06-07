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
