# IoC & Dependency Injection

Pancake provides two injection mechanisms: config-based auto-injection and object-based IoC container.

## @auto_inject

Automatically resolves function parameters from YAML/JSON config or registered instances.

Parameter types determine the source:
- `str` / `int` / `float` / `bool` → YAML config (parameter name `service_title` maps to `service.title`)
- `dict` / `list` → JSON config
- Other types → IoC container instances

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

# Call without arguments — auto-resolved from config
get_config()
```

### Parameter Name Mapping

Underscores in parameter names map to dots in config keys:

| Parameter Name | Config Key |
|----------------|------------|
| `service_title` | `service.title` |
| `mybatis_database_url` | `mybatis.database.url` |

## IoC Container

Manage object dependencies with three scopes.

### Scopes

| Scope | Description |
|-------|-------------|
| `Scope.SINGLETON` | Global single instance |
| `Scope.TRANSIENT` | New instance every time |
| `Scope.SCOPED` | Single instance per scope |

### Register & Resolve

```python
# Register
container.register(UserService, UserService, Scope.SINGLETON)
container.register(EmailService, EmailService, Scope.TRANSIENT)

# Register with factory
container.register(DbConnection, factory=lambda: create_connection(), scope=Scope.SINGLETON)

# Register shortcuts
container.register_singleton(UserService, UserService)
container.register_transient(EmailService, EmailService)
container.register_scoped(RequestHandler, RequestHandler)

# Resolve
service = container.resolve(UserService)
```

### Auto-Constructor Injection

The container automatically resolves constructor dependencies:

```python
class UserService:
    def __init__(self, db: Database, cache: CacheService):
        self.db = db
        self.cache = cache

container.register(Database, Database, Scope.SINGLETON)
container.register(CacheService, CacheService, Scope.SINGLETON)
container.register(UserService, UserService, Scope.SINGLETON)

# UserService automatically gets Database and CacheService injected
service = container.resolve(UserService)
```

### Circular Dependency Detection

The container raises `ValueError` if circular dependencies are detected:

```
ValueError: 检测到循环依赖: A -> B -> C -> A
```

## @inject

Inject dependencies from the IoC container into function parameters.

```python
@inject
def process(user_service: UserService, email_service: EmailService):
    # user_service and email_service auto-resolved from container
    ...
```

### Named Dependencies

```python
@inject(primary_db=Database, cache=RedisClient)
def setup(primary_db, cache):
    ...
```

## Global Container

A global container instance is available as `container` in builtins.

```python
# These are equivalent
container.register(UserService, UserService, Scope.SINGLETON)
```
