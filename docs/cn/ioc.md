# IoC 与依赖注入

Pancake 提供两种注入机制：基于配置的自动注入和基于对象的 IoC 容器。

## @auto_inject

自动从 YAML/JSON 配置或注册实例解析函数参数。

参数类型决定数据来源：
- `str` / `int` / `float` / `bool` → YAML 配置（参数名 `service_title` 映射到 `service.title`）
- `dict` / `list` → JSON 配置
- 其他类型 → IoC 容器实例

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

# 无参调用 — 自动从配置解析
get_config()
```

### 参数名映射

参数名中的下划线映射为配置键中的点：

| 参数名 | 配置键 |
|--------|--------|
| `service_title` | `service.title` |
| `mybatis_database_url` | `mybatis.database.url` |

## IoC 容器

使用三种作用域管理对象依赖。

### 作用域

| 作用域 | 说明 |
|--------|------|
| `Scope.SINGLETON` | 全局单例 |
| `Scope.TRANSIENT` | 每次创建新实例 |
| `Scope.SCOPED` | 同一作用域内单例 |

### 注册与解析

```python
# 注册
container.register(UserService, UserService, Scope.SINGLETON)
container.register(EmailService, EmailService, Scope.TRANSIENT)

# 工厂注册
container.register(DbConnection, factory=lambda: create_connection(), scope=Scope.SINGLETON)

# 快捷注册
container.register_singleton(UserService, UserService)
container.register_transient(EmailService, EmailService)
container.register_scoped(RequestHandler, RequestHandler)

# 解析
service = container.resolve(UserService)
```

### 自动构造函数注入

容器自动解析构造函数依赖：

```python
class UserService:
    def __init__(self, db: Database, cache: CacheService):
        self.db = db
        self.cache = cache

container.register(Database, Database, Scope.SINGLETON)
container.register(CacheService, CacheService, Scope.SINGLETON)
container.register(UserService, UserService, Scope.SINGLETON)

# UserService 自动注入 Database 和 CacheService
service = container.resolve(UserService)
```

### 循环依赖检测

容器检测到循环依赖时抛出 `ValueError`：

```
ValueError: 检测到循环依赖: A -> B -> C -> A
```

## @inject

从 IoC 容器注入依赖到函数参数。

```python
@inject
def process(user_service: UserService, email_service: EmailService):
    # user_service 和 email_service 自动从容器解析
    ...
```

### 命名依赖

```python
@inject(primary_db=Database, cache=RedisClient)
def setup(primary_db, cache):
    ...
```

## 全局容器

全局容器实例作为 `container` 注入到 builtins。

```python
# 以下等价
container.register(UserService, UserService, Scope.SINGLETON)
```
