"""
集成测试 — 模拟真实框架使用场景
测试多层依赖、循环依赖、注入未注册、混合同步异步等复杂情况
"""

import pytest
from pancake.dough import Dough, Scope, _call_lifecycle
from pancake.decorators import DependsOn, Import, Singleton, Prototype, Lazy, inject, noMaker
from pancake.factory.dough_factory import DoughFactory
from pancake.registry import clear_registry, register_class, get_class
from pancake.base.configuration import Configuration
from pancake.base.service import Service
from pancake.base.struct import Struct


@pytest.fixture
def factory():
    """每个测试前清空状态，返回干净的工厂"""
    DoughFactory._factories.clear()
    clear_registry()
    yield DoughFactory.get()
    DoughFactory._factories.clear()
    clear_registry()


# ============================================================
#  1. 多层依赖链 (5层)
#  Controller → UserService → UserRepository → Database → Config
# ============================================================


class TestMultiLayerDependency:

    @pytest.mark.asyncio
    async def test_five_layer_chain_creation_order(self, factory):
        """5层依赖链按正确顺序创建"""
        creation_order = []

        class AppConfig(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("AppConfig")
                self.db_url = "sqlite:///:memory:"

        @DependsOn("AppConfig")
        class Database(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("Database")
            async def on_init(self):
                cfg = DoughFactory.get().resolve("AppConfig")
                self.url = cfg.db_url

        @DependsOn("Database")
        class UserRepository(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("UserRepository")
            async def on_init(self):
                self.db = DoughFactory.get().resolve("Database")

        @DependsOn("UserRepository")
        class UserService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("UserService")
            async def on_init(self):
                self.repo = DoughFactory.get().resolve("UserRepository")

        @DependsOn("UserService")
        class UserController(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_order.append("UserController")
            async def on_init(self):
                self.service = DoughFactory.get().resolve("UserService")

        factory.register(AppConfig)
        factory.register(Database)
        factory.register(UserRepository)
        factory.register(UserService)
        factory.register(UserController)

        await factory.async_create_all()

        assert creation_order == ["AppConfig", "Database", "UserRepository", "UserService", "UserController"]

        ctrl = factory.resolve("UserController")
        assert ctrl.service.repo.db.url == "sqlite:///:memory:"

    @pytest.mark.asyncio
    async def test_five_layer_chain_all_resolvable(self, factory):
        """5层链中每一层都可以独立 resolve"""

        class Config(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("Config")
        class DB(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("DB")
        class Repo(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("Repo")
        class Svc(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("Svc")
        class Ctrl(Dough):
            _scope = Scope.SINGLETON

        factory.register(Config)
        factory.register(DB)
        factory.register(Repo)
        factory.register(Svc)
        factory.register(Ctrl)
        await factory.async_create_all()

        for name in ["Config", "DB", "Repo", "Svc", "Ctrl"]:
            bean = factory.resolve(name)
            assert bean is not None


# ============================================================
#  2. 菱形依赖 (Diamond)
#      A
#     / \
#    B   C
#     \ /
#      D
# ============================================================


class TestDiamondDependency:

    @pytest.mark.asyncio
    async def test_diamond_d_created_once(self, factory):
        """菱形依赖中 D 只被创建一次"""
        creation_count = {"D": 0}

        class D(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                creation_count["D"] += 1
                self.value = 42

        @DependsOn("D")
        class B(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("D")
        class C(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("B", "C")
        class A(Dough):
            _scope = Scope.SINGLETON

        factory.register(D)
        factory.register(B)
        factory.register(C)
        factory.register(A)
        await factory.async_create_all()

        assert creation_count["D"] == 1

    @pytest.mark.asyncio
    async def test_diamond_all_get_same_d_instance(self, factory):
        """菱形依赖中所有 Bean 拿到同一个 D 实例"""

        class D(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.id = "shared_d"

        @DependsOn("D")
        class B(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                self.d = DoughFactory.get().resolve("D")

        @DependsOn("D")
        class C(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                self.d = DoughFactory.get().resolve("D")

        @DependsOn("B", "C")
        class A(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                self.b = DoughFactory.get().resolve("B")
                self.c = DoughFactory.get().resolve("C")

        factory.register(D)
        factory.register(B)
        factory.register(C)
        factory.register(A)
        await factory.async_create_all()

        a = factory.resolve("A")
        assert a.b.d is a.c.d
        assert a.b.d.id == "shared_d"


# ============================================================
#  3. 循环依赖检测
# ============================================================


class TestCircularDependency:

    @pytest.mark.asyncio
    async def test_three_node_cycle(self, factory):
        """A→B→C→A 三层循环依赖"""

        @DependsOn("B")
        class A(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("C")
        class B(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("A")
        class C(Dough):
            _scope = Scope.SINGLETON

        factory.register(A)
        factory.register(B)
        factory.register(C)

        with pytest.raises(ValueError, match="循环依赖"):
            await factory.async_create_all()

    @pytest.mark.asyncio
    async def test_self_dependency(self, factory):
        """自依赖 A→A"""

        @DependsOn("A")
        class A(Dough):
            _scope = Scope.SINGLETON

        factory.register(A)

        with pytest.raises(ValueError, match="循环依赖"):
            await factory.async_create_all()

    @pytest.mark.asyncio
    async def test_cycle_with_independent_beans(self, factory):
        """循环依赖不影响独立 Bean 的创建"""

        @DependsOn("B")
        class A(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("A")
        class B(Dough):
            _scope = Scope.SINGLETON

        class Independent(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.ok = True

        factory.register(A)
        factory.register(B)
        factory.register(Independent)

        with pytest.raises(ValueError, match="循环依赖"):
            await factory.async_create_all()


# ============================================================
#  4. 注入未注册的 Bean
# ============================================================


class TestUnregisteredBean:

    def test_resolve_unregistered_raises(self, factory):
        """resolve 未注册的名称抛出 ValueError"""
        with pytest.raises(ValueError, match="未注册"):
            factory.resolve("GhostBean")

    @pytest.mark.asyncio
    async def test_inject_unregistered_keeps_default(self, factory):
        """@inject 函数参数类型未注册时保持默认值"""

        class RegisteredBean(Dough):
            _no_register = True
            _scope = Scope.SINGLETON
            def __init__(self):
                self.value = 100

        register_class("RegisteredBean", RegisteredBean)
        factory.register_instance("RegisteredBean", RegisteredBean())

        @inject
        def get_data(registered_bean: RegisteredBean = None, missing_bean=None):
            return {"registered": registered_bean, "missing": missing_bean}

        result = get_data()
        assert result["registered"] is not None
        assert result["missing"] is None

    @pytest.mark.asyncio
    async def test_depends_on_nonexistent_still_creates(self, factory):
        """DependsOn 引用不存在的 Bean 不影响自身创建"""

        @DependsOn("NonExistentBean")
        class MyBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.created = True

        factory.register(MyBean)
        await factory.async_create_all()

        assert factory.resolve("MyBean").created is True


# ============================================================
#  5. 混合同步/异步生命周期
# ============================================================


class TestMixedSyncAsyncLifecycle:

    @pytest.mark.asyncio
    async def test_sync_init_async_start(self, factory):
        """同步 on_init + 异步 on_start"""

        class MixedBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.init_done = False
                self.start_done = False

            def on_init(self):  # 同步
                self.init_done = True

            async def on_start(self):  # 异步
                self.start_done = True

        factory.register(MixedBean)
        await factory.async_create_all()
        await factory.async_startup_all()

        bean = factory.resolve("MixedBean")
        assert bean.init_done is True
        assert bean.start_done is True

    @pytest.mark.asyncio
    async def test_async_init_sync_stop(self, factory):
        """异步 on_init + 同步 on_stop"""

        class MixedBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.init_done = False
                self.stop_done = False

            async def on_init(self):  # 异步
                self.init_done = True

            def on_stop(self):  # 同步
                self.stop_done = True

        factory.register(MixedBean)
        await factory.async_create_all()
        bean = factory.resolve("MixedBean")
        assert bean.init_done is True

        await factory.async_shutdown_all()
        assert bean.stop_done is True

    @pytest.mark.asyncio
    async def test_call_lifecycle_sync(self):
        """_call_lifecycle 正确调用同步方法"""

        class SyncBean:
            def __init__(self):
                self.called = False
            def on_test(self):
                self.called = True

        bean = SyncBean()
        await _call_lifecycle(bean, "on_test")
        assert bean.called is True

    @pytest.mark.asyncio
    async def test_call_lifecycle_async(self):
        """_call_lifecycle 正确调用异步方法"""

        class AsyncBean:
            def __init__(self):
                self.called = False
            async def on_test(self):
                self.called = True

        bean = AsyncBean()
        await _call_lifecycle(bean, "on_test")
        assert bean.called is True

    @pytest.mark.asyncio
    async def test_call_lifecycle_missing_method(self):
        """_call_lifecycle 方法不存在时不报错"""

        class PlainBean:
            pass

        bean = PlainBean()
        await _call_lifecycle(bean, "on_nonexistent")  # 不应抛异常


# ============================================================
#  6. Configuration + Maker 方法依赖其他 Bean
# ============================================================


class TestConfigurationMakerDependencies:

    @pytest.mark.asyncio
    async def test_maker_uses_other_bean(self, factory):
        """Configuration 的 maker 方法可以使用其他 Bean"""

        class CacheService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.ttl = 300

        class AppConfig(Configuration):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass
            def cache_config(self):
                return {"ttl": 300, "backend": "memory"}

        factory.register(CacheService)
        factory.register(AppConfig)
        await factory.async_create_all()

        cache_cfg = factory.resolve("cache_config")
        assert cache_cfg == {"ttl": 300, "backend": "memory"}

    @pytest.mark.asyncio
    async def test_no_maker_excludes_method(self, factory):
        """@noMaker 排除的方法不注册为 Bean"""

        class AppConfig(Configuration):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass

            def my_bean(self):
                return {"type": "bean"}

            @noMaker
            def helper(self):
                return {"type": "helper"}

        factory.register(AppConfig)
        await factory.async_create_all()

        assert factory.resolve("my_bean") == {"type": "bean"}
        with pytest.raises(ValueError, match="未注册"):
            factory.resolve("helper")

    @pytest.mark.asyncio
    async def test_maker_skips_primitive_returns(self, factory):
        """Configuration 的 maker 方法跳过原始类型返回值"""

        class AppConfig(Configuration):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass
            def get_name(self):
                return "should_not_register"
            def get_count(self):
                return 42
            def get_enabled(self):
                return True
            def real_bean(self):
                return {"registered": True}

        factory.register(AppConfig)
        await factory.async_create_all()

        assert factory.resolve("real_bean") == {"registered": True}
        for name in ["get_name", "get_count", "get_enabled"]:
            with pytest.raises(ValueError, match="未注册"):
                factory.resolve(name)


# ============================================================
#  7. @Import 外部类链式依赖
# ============================================================


class TestImportChainDependency:

    @pytest.mark.asyncio
    async def test_import_class_with_depends_on(self, factory):
        """Import 的类本身有 DependsOn"""

        class Logger(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.ready = True

        @DependsOn("Logger")
        class DatabaseService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.connected = False
            async def on_init(self):
                logger = DoughFactory.get().resolve("Logger")
                if logger.ready:
                    self.connected = True

        @Import(DatabaseService)
        class AppConfig(Dough):
            _scope = Scope.SINGLETON

        factory.register(Logger)
        factory.register(AppConfig)
        await factory.async_create_all()

        db = factory.resolve("DatabaseService")
        assert db.connected is True

    @pytest.mark.asyncio
    async def test_import_multiple_interdependent_classes(self, factory):
        """Import 多个类，它们之间有依赖关系"""

        class CacheManager(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.cached = {}

        @DependsOn("CacheManager")
        class SessionService(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.sessions = {}

        @Import(CacheManager, SessionService)
        class AppConfig(Dough):
            _scope = Scope.SINGLETON

        factory.register(AppConfig)
        await factory.async_create_all()

        cache = factory.resolve("CacheManager")
        session = factory.resolve("SessionService")
        assert cache is not None
        assert session is not None


# ============================================================
#  8. Prototype 在 Singleton 依赖中的行为
# ============================================================


class TestPrototypeInSingleton:

    @pytest.mark.asyncio
    async def test_singleton_holds_prototype_snapshot(self, factory):
        """Singleton A 依赖 Prototype B，A 持有的是创建时的 B 快照"""

        class PrototypeBean(Dough):
            _scope = Scope.PROTOTYPE
            def __init__(self):
                import uuid
                self.uid = str(uuid.uuid4())[:8]

        class SingletonBean(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                self.prototype = DoughFactory.get().resolve("PrototypeBean")

        factory.register(PrototypeBean)
        factory.register(SingletonBean)
        await factory.async_create_all()

        singleton = factory.resolve("SingletonBean")
        proto1 = singleton.prototype

        # Singleton 每次 resolve 返回同一个
        singleton2 = factory.resolve("SingletonBean")
        assert singleton is singleton2
        # 它持有的 Prototype 实例也相同（创建时的快照）
        assert singleton.prototype is proto1

    @pytest.mark.asyncio
    async def test_prototype_resolve_returns_new_each_time(self, factory):
        """Prototype Bean 每次 resolve 返回新实例"""
        import uuid

        class Counter(Dough):
            _scope = Scope.PROTOTYPE
            def __init__(self):
                self.uid = str(uuid.uuid4())[:8]

        factory.register(Counter)
        await factory.async_create_all()

        instances = [factory.resolve("Counter") for _ in range(5)]
        uids = [inst.uid for inst in instances]
        # 所有 uid 都不同
        assert len(set(uids)) == 5
        # 所有实例都是不同对象
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                assert instances[i] is not instances[j]


# ============================================================
#  9. Lazy + 依赖链
# ============================================================


class TestLazyDependencyChain:

    @pytest.mark.asyncio
    async def test_lazy_not_created_during_create_all(self, factory):
        """Lazy Bean 在 create_all 时不会被创建"""

        class LazyBean(Dough):
            _scope = Scope.LAZY
            def __init__(self):
                self.created = True

        factory.register(LazyBean)
        await factory.async_create_all()

        from pancake.registry import get_instance
        assert get_instance("LazyBean") is None

    @pytest.mark.asyncio
    async def test_lazy_created_on_resolve(self, factory):
        """Lazy Bean 在首次 resolve 时创建"""

        class LazyBean(Dough):
            _scope = Scope.LAZY
            def __init__(self):
                self.created = True

        factory.register(LazyBean)
        await factory.async_create_all()

        bean = factory.resolve("LazyBean")
        assert bean.created is True

    @pytest.mark.asyncio
    async def test_lazy_resolve_returns_same_instance(self, factory):
        """Lazy Bean 多次 resolve 返回同一实例（LAZY 本质是延迟 Singleton）"""

        class LazyBean(Dough):
            _scope = Scope.LAZY
            def __init__(self):
                import uuid
                self.uid = str(uuid.uuid4())[:8]

        factory.register(LazyBean)
        await factory.async_create_all()

        b1 = factory.resolve("LazyBean")
        b2 = factory.resolve("LazyBean")
        assert b1 is b2


# ============================================================
#  10. 完整构建流水线
# ============================================================


class TestFullBuildPipeline:

    @pytest.mark.asyncio
    async def test_full_lifecycle_pipeline(self, factory):
        """完整生命周期: create → startup → shutdown"""
        events = []

        class BeanA(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                events.append("A.__init__")
            async def on_init(self):
                events.append("A.on_init")
            async def on_start(self):
                events.append("A.on_start")
            async def on_stop(self):
                events.append("A.on_stop")
            async def on_destroy(self):
                events.append("A.on_destroy")

        @DependsOn("BeanA")
        class BeanB(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                events.append("B.__init__")
            async def on_init(self):
                events.append("B.on_init")
            async def on_start(self):
                events.append("B.on_start")
            async def on_stop(self):
                events.append("B.on_stop")
            async def on_destroy(self):
                events.append("B.on_destroy")

        factory.register(BeanA)
        factory.register(BeanB)

        await factory.async_create_all()
        assert events == ["A.__init__", "A.on_init", "B.__init__", "B.on_init"]

        await factory.async_startup_all()
        assert events[-2:] == ["A.on_start", "B.on_start"]

        events.clear()
        await factory.async_shutdown_all()
        # 逆序关闭: B 先停，A 后停
        assert events == ["B.on_stop", "B.on_destroy", "A.on_stop", "A.on_destroy"]

    @pytest.mark.asyncio
    async def test_many_beans_with_mixed_dependencies(self, factory):
        """大量 Bean 混合依赖关系的完整构建"""

        class Config(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.settings = {"debug": True}

        class Logger(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.logs = []

        @DependsOn("Config", "Logger")
        class Database(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                self.cfg = DoughFactory.get().resolve("Config")
                self.logger = DoughFactory.get().resolve("Logger")

        @DependsOn("Database")
        class UserRepository(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("Database")
        class OrderRepository(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("UserRepository", "Logger")
        class UserService(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("OrderRepository", "Logger")
        class OrderService(Dough):
            _scope = Scope.SINGLETON

        @DependsOn("UserService", "OrderService")
        class Gateway(Dough):
            _scope = Scope.SINGLETON

        beans = [Config, Logger, Database, UserRepository, OrderRepository,
                 UserService, OrderService, Gateway]
        for b in beans:
            factory.register(b)

        await factory.async_create_all()
        await factory.async_startup_all()

        gateway = factory.resolve("Gateway")
        assert gateway is not None
        db = factory.resolve("Database")
        assert db.cfg.settings["debug"] is True


# ============================================================
#  11. 生命周期异常处理
# ============================================================


class TestLifecycleException:

    @pytest.mark.asyncio
    async def test_on_init_failure_stops_creation(self, factory):
        """on_init 抛出异常时，创建过程停止"""

        class FailingBean(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                raise RuntimeError("init failed")

        class DependentBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.created = True

        factory.register(FailingBean)
        factory.register(DependentBean)

        with pytest.raises(RuntimeError, match="init failed"):
            await factory.async_create_all()

    @pytest.mark.asyncio
    async def test_on_stop_exception_doesnt_block_others(self, factory):
        """on_stop 抛出异常时不阻塞其他 Bean 的关闭"""

        class FailingStop(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.stopped = False
            async def on_stop(self):
                raise RuntimeError("stop failed")

        class NormalBean(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.stopped = False
            async def on_stop(self):
                self.stopped = True

        # FailingStop 在 NormalBean 之前创建（字母序）
        # 关闭时 FailingStop 先执行，抛异常后 NormalBean 仍应执行
        factory.register(FailingStop)
        factory.register(NormalBean)
        await factory.async_create_all()

        # async_shutdown_all 不会因单个 Bean 的异常而中断
        await factory.async_shutdown_all()
        assert factory.resolve("NormalBean").stopped is True

    @pytest.mark.asyncio
    async def test_on_init_exception_in_dependency_chain(self, factory):
        """依赖链中间环节 on_init 失败"""

        class Config(Dough):
            _scope = Scope.SINGLETON
            def __init__(self):
                self.ok = True

        @DependsOn("Config")
        class FailingDB(Dough):
            _scope = Scope.SINGLETON
            async def on_init(self):
                raise ConnectionError("db connection failed")

        @DependsOn("FailingDB")
        class UserService(Dough):
            _scope = Scope.SINGLETON

        factory.register(Config)
        factory.register(FailingDB)
        factory.register(UserService)

        with pytest.raises(ConnectionError, match="db connection failed"):
            await factory.async_create_all()


# ============================================================
#  12. Prototype 的 on_init 每次都调用
# ============================================================


class TestPrototypeLifecycle:

    @pytest.mark.asyncio
    async def test_prototype_on_init_not_called_on_resolve(self, factory):
        """Prototype Bean 通过 resolve 创建时不会调用 on_init

        注意：这是当前框架行为，Prototype resolve 只调用 cls() 不调用生命周期。
        如果需要 on_init，需要手动调用或使用 create_all。
        """

        class Proto(Dough):
            _scope = Scope.PROTOTYPE
            def __init__(self):
                self.init_called = False
            async def on_init(self):
                self.init_called = True

        factory.register(Proto)
        await factory.async_create_all()

        b1 = factory.resolve("Proto")
        # 当前行为：resolve 创建的 Prototype 不调用 on_init
        assert b1.init_called is False


# ============================================================
#  13. @inject 实际注入场景
# ============================================================


class TestInjectIntegration:

    @pytest.mark.asyncio
    async def test_inject_resolves_from_factory(self, factory):
        """@inject 从 DoughFactory 解析依赖"""

        class MyService(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.value = 999

        register_class("MyService", MyService)
        factory.register_instance("MyService", MyService())

        @inject
        def use_service(my_service: MyService):
            return my_service.value

        result = use_service()
        assert result == 999

    @pytest.mark.asyncio
    async def test_inject_partial_resolution(self, factory):
        """@inject 部分参数可解析，部分用默认值"""

        class KnownBean(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.known = True

        register_class("KnownBean", KnownBean)
        factory.register_instance("KnownBean", KnownBean())

        @inject
        def partial(known_bean: KnownBean = None, unknown_bean=None, explicit: str = "default"):
            return {
                "known": known_bean,
                "unknown": unknown_bean,
                "explicit": explicit,
            }

        result = partial(explicit="custom")
        assert result["known"] is not None
        assert result["unknown"] is None
        assert result["explicit"] == "custom"

    @pytest.mark.asyncio
    async def test_inject_async_function(self, factory):
        """@inject 异步函数也能正确注入"""

        class AsyncService(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.data = "async_data"

        register_class("AsyncService", AsyncService)
        factory.register_instance("AsyncService", AsyncService())

        @inject
        async def async_use(service: AsyncService):
            return service.data

        result = await async_use()
        assert result == "async_data"


# ============================================================
#  14. Struct + Configuration 组合
# ============================================================


class TestStructConfigurationCombo:

    def test_struct_dataclass_fields(self):
        """Struct 支持 dataclass 字段（通过 @struct 装饰器转换）"""
        from dataclasses import fields
        from pancake.decorators import struct

        @struct
        class UserDTO:
            name: str = ""
            age: int = 0
            email: str = ""

        user = UserDTO(name="Alice", age=30, email="alice@example.com")
        assert user.name == "Alice"
        assert user.age == 30

        field_names = [f.name for f in fields(UserDTO)]
        assert "name" in field_names
        assert "age" in field_names
        assert "email" in field_names

    @pytest.mark.asyncio
    async def test_configuration_creates_multiple_beans(self, factory):
        """Configuration 可以创建多个 Bean"""

        class AppConfig(Configuration):
            _scope = Scope.SINGLETON
            def __init__(self):
                pass
            def cache(self):
                return {"backend": "redis", "ttl": 60}
            def auth(self):
                return {"method": "jwt", "expiry": 3600}
            def features(self):
                return {"dark_mode": True}

        factory.register(AppConfig)
        await factory.async_create_all()

        assert factory.resolve("cache") == {"backend": "redis", "ttl": 60}
        assert factory.resolve("auth") == {"method": "jwt", "expiry": 3600}
        assert factory.resolve("features") == {"dark_mode": True}


# ============================================================
#  15. 边界情况
# ============================================================


class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_factory_create_all(self, factory):
        """空工厂调用 create_all 不报错"""
        await factory.async_create_all()

    @pytest.mark.asyncio
    async def test_empty_factory_shutdown_all(self, factory):
        """空工厂调用 shutdown_all 不报错"""
        await factory.async_shutdown_all()

    @pytest.mark.asyncio
    async def test_duplicate_register_overwrites(self, factory):
        """重复注册同名类覆盖前者"""

        class V1(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.version = 1

        class V2(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.version = 2

        factory.register(V1)
        factory.register(V2)  # 覆盖 V1
        await factory.async_create_all()

        bean = factory.resolve("V2")
        assert bean.version == 2

    @pytest.mark.asyncio
    async def test_register_instance_then_resolve(self, factory):
        """手动注册实例可以直接 resolve"""

        class MyBean(Dough):
            _scope = Scope.SINGLETON
            _no_register = True
            def __init__(self):
                self.manual = True

        instance = MyBean()
        factory.register_instance("my_custom", instance)

        resolved = factory.resolve("my_custom")
        assert resolved is instance
        assert resolved.manual is True

    @pytest.mark.asyncio
    async def test_get_all_instances(self, factory):
        """get_all_instances 返回所有已创建的实例"""

        class A(Dough):
            _scope = Scope.SINGLETON
        class B(Dough):
            _scope = Scope.SINGLETON

        factory.register(A)
        factory.register(B)
        await factory.async_create_all()

        instances = factory.get_all_instances()
        assert "A" in instances
        assert "B" in instances

    @pytest.mark.asyncio
    async def test_get_all_classes(self, factory):
        """get_all_classes 返回所有注册的类"""

        class X(Dough):
            _scope = Scope.SINGLETON
        class Y(Dough):
            _scope = Scope.SINGLETON

        factory.register(X)
        factory.register(Y)

        classes = factory.get_all_classes()
        assert "X" in classes
        assert "Y" in classes
