# 2. 核心概念

[← 上一节](01-quickstart.md) | [下一节 →](03-ioc.md)

---

## Dough — Bean 基类

`Dough` 是所有框架类型的基类，类似于 Spring 的 `Object`。所有自定义 Bean 都应继承 `Dough` 或其子类。

```python
class MyBean(Dough):
    async def on_init(self):
        # 初始化后调用（@PostConstruct）
        pass

    async def on_start(self):
        # 就绪后调用
        pass

    async def on_stop(self):
        # 停止时调用
        pass

    async def on_destroy(self):
        # 销毁前调用（@PreDestroy）
        pass
```

## 生命周期

```
__init__()  →  on_init()  →  on_start()  →  [运行中]  →  on_stop()  →  on_destroy()
   构造        @PostConstruct    就绪                        停止         @PreDestroy
```

所有生命周期方法支持同步和异步实现，`DoughFactory` 会自动检测并正确调用。

```python
# 同步
class SyncBean(Dough):
    def on_init(self):
        print("initialized")

# 异步
class AsyncBean(Dough):
    async def on_init(self):
        await some_async_operation()
```

## 作用域

| 作用域 | 装饰器 | 说明 |
|--------|--------|------|
| 单例 | `@singleton` | 每个工厂一个实例（默认） |
| 多例 | `@prototype` | 每次获取创建新实例 |
| 懒加载 | `@lazy` | 首次访问时创建 |

```python
@singleton
class MyService(Service):
    pass

@prototype
class MyPrototype(Service):
    pass

@lazy
class MyLazy(Service):
    pass
```

## 基类体系

| 基类 | 用途 | 示例 |
|------|------|------|
| `Service` | 服务类，方法集合 | `UserService`、`OrderService` |
| `Configuration` | 配置类，方法返回值自动注册为 Bean | `AppConfig`、`DatabaseConfig` |
| `Struct` | 数据结构（dataclass） | `User`、`OrderForm` |
| `Function` | 函数包装 | `FormatDate`、`ValidateEmail` |

### Service

```python
class UserService(Service):
    async def find_user(self, user_id: int):
        return {"id": user_id, "name": "Alice"}
```

### Configuration

```python
@configuration
class AppConfig(Configuration):
    def cache_manager(self):
        """返回值自动注册为 Bean"""
        return CacheManager()

    @no_maker
    def helper(self):
        return "not a bean"
```

### Struct

```python
@struct
class UserForm:
    name: str = None
    email: str = None
    age: int = None

form = UserForm(name="Alice", email="alice@example.com", age=25)
```

### Function

```python
@function
def format_date(date_str: str) -> str:
    from datetime import datetime
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")

result = format_date("2024-01-15")  # "15/01/2024"
```

---

[← 上一节](01-quickstart.md) | [下一节 →](03-ioc.md)
