# 3. IoC Container

[← Previous](02-core-concepts.md) | [Next →](04-config.md)

---

## Registering Beans

Beans are registered to the IoC container via:

1. **Extending Dough subclasses** — `DoughMeta` metaclass auto-registers
2. **@service / @configuration** — type conversion decorators
3. **Configuration method return values** — auto-register
4. **Manual registration** — `DoughFactory.get().register(cls)`

## Dependency Injection

### @inject — Inject by Type

```python
@singleton
class OrderService(Service):
    async def on_init(self):
        # Manual resolve
        self.user_service = DoughFactory.get().resolve("UserService")

    @inject
    async def create_order(self, user: UserService):
        # Parameter auto-injected by type
        return await user.get_user(1)
```

### @inject on Classes — Auto-inject Attributes

```python
@singleton
@inject
class OrderService(Service):
    user_service: UserService  # Auto-injected
    db: Database               # Auto-injected

    async def on_init(self):
        # user_service and db are already injected
        pass
```

### @inject_name — Inject by Name

```python
@inject
async def my_func(primary_db = inject_name("primary_db")):
    # Inject by specified name
    pass
```

## @depends_on — Declare Dependencies

```python
@singleton
@depends_on("DatabaseService", "CacheService")
class UserService(Service):
    async def on_init(self):
        # DatabaseService and CacheService already created before this
        self.db = DoughFactory.get().resolve("DatabaseService")
        self.cache = DoughFactory.get().resolve("CacheService")
```

`DoughFactory` uses Kahn's algorithm for topological sorting, ensuring dependencies are created before dependents. Circular dependencies raise `ValueError`.

## @import_class — Import External Classes

```python
@configuration
@import_class(ExternalServiceA, ExternalServiceB)
class AppConfig(Configuration):
    pass
# ExternalServiceA and ExternalServiceB are auto-registered to factory
```

## Configuration — Bean Factory

Non-private method return values of `Configuration` classes auto-register as Beans:

```python
@configuration
class AppConfig(Configuration):
    def cache_manager(self):
        """Return auto-registers as Bean"""
        return CacheManager()

    def database(self):
        return Database("sqlite:///app.db")

    @maker("my_cache")  # Custom Bean name
    def create_cache(self):
        return RedisCache()

    @no_maker  # Exclude, don't register
    def helper(self):
        return "not a bean"
```

## Resolving Beans

```python
# Resolve by name
service = DoughFactory.get().resolve("UserService")

# All instances
instances = DoughFactory.get().get_all_instances()

# All registered classes
classes = DoughFactory.get().get_all_classes()
```

---

[← Previous](02-core-concepts.md) | [Next →](04-config.md)
