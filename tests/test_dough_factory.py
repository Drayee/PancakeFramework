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


class TestDependencyResolution:

    def setup_method(self):
        DoughFactory._factories.clear()

    def test_depends_on_creates_in_order(self):
        """@DependsOn 确保依赖先创建"""
        from pancake.decorators import DependsOn

        class DatabaseService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.connected = True

        @DependsOn("DatabaseService")
        class UserService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.db_ready = False
            def on_init(self):
                # DatabaseService should already be created
                db = DoughFactory.get().resolve("DatabaseService")
                self.db_ready = db.connected

        factory = DoughFactory.get()
        factory.register(DatabaseService)
        factory.register(UserService)
        factory.create_all()

        user_svc = factory.resolve("UserService")
        assert user_svc.db_ready is True

    def test_circular_dependency_raises(self):
        """循环依赖应该报错"""
        from pancake.decorators import DependsOn

        @DependsOn("ServiceB")
        class ServiceA(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass

        @DependsOn("ServiceA")
        class ServiceB(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass

        factory = DoughFactory.get()
        factory.register(ServiceA)
        factory.register(ServiceB)

        with pytest.raises(ValueError, match="循环依赖"):
            factory.create_all()

    def test_import_registers_classes(self):
        """@Import 自动注册外部类"""
        from pancake.decorators import Import

        class ExternalService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.value = 99

        @Import(ExternalService)
        class AppConfig(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass

        factory = DoughFactory.get()
        factory.register(AppConfig)
        factory.create_all()

        # ExternalService should be auto-registered and created
        ext = factory.resolve("ExternalService")
        assert ext.value == 99

    def test_chained_dependencies(self):
        """链式依赖 A -> B -> C，创建顺序应为 C, B, A"""
        from pancake.decorators import DependsOn

        creation_order = []

        class ServiceC(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("ServiceC")

        @DependsOn("ServiceC")
        class ServiceB(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("ServiceB")

        @DependsOn("ServiceB")
        class ServiceA(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("ServiceA")

        factory = DoughFactory.get()
        factory.register(ServiceA)
        factory.register(ServiceB)
        factory.register(ServiceC)
        factory.create_all()

        assert creation_order == ["ServiceC", "ServiceB", "ServiceA"]

    def test_no_dependencies_still_works(self):
        """无依赖的 Bean 正常创建"""
        class SimpleBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.ok = True

        factory = DoughFactory.get()
        factory.register(SimpleBean)
        factory.create_all()
        assert factory.resolve("SimpleBean").ok is True

    def test_depends_on_unknown_bean_ignored(self):
        """依赖未注册的 Bean 时，拓扑排序忽略该依赖（不阻塞）"""
        from pancake.decorators import DependsOn

        @DependsOn("NonExistentBean")
        class MyBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.created = True

        factory = DoughFactory.get()
        factory.register(MyBean)
        factory.create_all()
        assert factory.resolve("MyBean").created is True
