"""测试 broker.py 模块级可变状态修复

验证 SubscriptionRegistry 可以重置，on_event handler 可以取消。
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_subscription_registry_basic():
    """SubscriptionRegistry 基本功能"""
    from pancake.ovenware.broker import SubscriptionRegistry

    registry = SubscriptionRegistry()

    def handler1(msg):
        pass

    def handler2(msg):
        pass

    registry.add("event1", handler1)
    registry.add("event1", handler2)
    registry.add("event2", handler1)

    all_handlers = registry.get_all()
    assert len(all_handlers["event1"]) == 2
    assert len(all_handlers["event2"]) == 1
    print("[OK] SubscriptionRegistry 基本功能正常")


def test_subscription_registry_remove():
    """可以取消注册 handler"""
    from pancake.ovenware.broker import SubscriptionRegistry

    registry = SubscriptionRegistry()

    def handler1(msg):
        pass

    def handler2(msg):
        pass

    registry.add("event1", handler1)
    registry.add("event1", handler2)

    registry.remove("event1", handler1)

    all_handlers = registry.get_all()
    assert len(all_handlers["event1"]) == 1
    assert all_handlers["event1"][0] is handler2
    print("[OK] 取消注册 handler 正常")


def test_subscription_registry_clear():
    """可以清空所有 handler"""
    from pancake.ovenware.broker import SubscriptionRegistry

    registry = SubscriptionRegistry()

    def handler(msg):
        pass

    registry.add("event1", handler)
    registry.add("event2", handler)

    registry.clear()

    all_handlers = registry.get_all()
    assert len(all_handlers) == 0
    print("[OK] 清空所有 handler 正常")


def test_no_duplicate_handlers():
    """同一个 handler 不会重复注册"""
    from pancake.ovenware.broker import SubscriptionRegistry

    registry = SubscriptionRegistry()

    def handler(msg):
        pass

    registry.add("event1", handler)
    registry.add("event1", handler)  # 重复添加

    all_handlers = registry.get_all()
    assert len(all_handlers["event1"]) == 1
    print("[OK] 重复注册被阻止")


def test_get_all_returns_copy():
    """get_all 返回副本，不影响内部状态"""
    from pancake.ovenware.broker import SubscriptionRegistry

    registry = SubscriptionRegistry()

    def handler(msg):
        pass

    registry.add("event1", handler)

    all_handlers = registry.get_all()
    all_handlers["event1"].clear()  # 清空副本

    # 内部状态不受影响
    all_handlers2 = registry.get_all()
    assert len(all_handlers2["event1"]) == 1
    print("[OK] get_all 返回副本，内部状态不受影响")


if __name__ == "__main__":
    test_subscription_registry_basic()
    test_subscription_registry_remove()
    test_subscription_registry_clear()
    test_no_duplicate_handlers()
    test_get_all_returns_copy()
    print("\n所有测试通过！")
