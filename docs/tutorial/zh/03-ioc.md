# 3. IoC 容器

[← 上一节](02-core-concepts.md) | [下一节 →](04-config.md)

---

## 注册 Bean

Bean 通过以下方式注册到 IoC 容器：

1. **继承 Dough 子类** — `DoughMeta` 元类自动注册
2. **@service / @configuration** — 类型转换装饰器
3. **Configuration 方法返回值** — 自动注册
4. **手动注册** — `DoughFactory.get().register(cls)`

## 依赖注入

### @inject — 按类型注入

```python
@singleton
class OrderService(Service):
    async def on_init(self):
        # 手动解析
        self.user_service = DoughFactory.get().resolve("UserService")

    @inject
    async def create_order(self, user: UserService):
        # 参数自动按类型注入
        return await user.get_user(1)
```

### @inject 用于类 — 自动注入属性

```python
@singleton
@inject
class OrderService(Service):
    user_service: UserService  # 自动注入
    db: Database               # 自动注入

    async def on_init(self):
        # user_service 和 db 已经注入完成
        pass
```

### @inject_name — 按名称注入

```python
@inject
async def my_func(primary_db = inject_name("primary_db")):
    # 按指定名称注入
    pass
```

## @depends_on — 声明依赖

```python
@singleton
@depends_on("DatabaseService", "CacheService")
class UserService(Service):
    async def on_init(self):
        # DatabaseService 和 CacheService 已在此前创建
        self.db = DoughFactory.get().resolve("DatabaseService")
        self.cache = DoughFactory.get().resolve("CacheService")
```

`DoughFactory` 使用 Kahn 算法进行拓扑排序，确保依赖先于被依赖者创建。检测到循环依赖时会抛出 `ValueError`。

## @import_class — 导入外部类

```python
@configuration
@import_class(ExternalServiceA, ExternalServiceB)
class AppConfig(Configuration):
    pass
# ExternalServiceA 和 ExternalServiceB 会被自动注册到工厂
```

## Configuration — Bean 工厂

`Configuration` 类的非私有方法返回值自动注册为 Bean：

```python
@configuration
class AppConfig(Configuration):
    def cache_manager(self):
        """返回值自动注册为 Bean"""
        return CacheManager()

    def database(self):
        return Database("sqlite:///app.db")

    @maker("my_cache")  # 自定义 Bean 名称
    def create_cache(self):
        return RedisCache()

    @no_maker  # 排除，不注册
    def helper(self):
        return "not a bean"
```

## 解析 Bean

```python
# 按名称解析
service = DoughFactory.get().resolve("UserService")

# 所有实例
instances = DoughFactory.get().get_all_instances()

# 所有注册的类
classes = DoughFactory.get().get_all_classes()
```

---

[← 上一节](02-core-concepts.md) | [下一节 →](04-config.md)
