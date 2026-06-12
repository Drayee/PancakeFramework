# 6. Embed Plugin — Zero Import

[← Previous](05-plugin-system.md) | [Next →](07-mybatis.md)

---

## Overview

`pancake-embed` is one of Pancake's most important plugins. It implements the "zero import" mechanism — when enabled, all framework decorators, base classes, and services are auto-injected into Python's `builtins` module. No `import` statements needed in user code.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>embed</artifactId>
</dependency>
```

## How It Works

Embed plugin loads at `init_order=999` (last):

1. Scans `registry.flour` (decorators), `water` (classes), `egg` (methods), `sugar` (other)
2. Injects all registered names into `builtins`
3. Patches `DoughMeta` metaclass — subsequent Dough subclasses auto-inject
4. Patches `register_decorator` — subsequent decorator registrations auto-inject

## Effect

Before (requires import):

```python
from pancake import Service, singleton, inject
from pancake_mybatis import Mapper, BaseMapper, Select

@singleton
class UserService(Service):
    pass
```

After (no import needed):

```python
@singleton
class UserService(Service):
    pass

@Mapper
class UserMapper(BaseMapper):
    @Select("SELECT * FROM users")
    async def find_all(self): ...
```

## What Gets Injected

| Source | Content | Examples |
|--------|---------|----------|
| `flour` | Decorators | `@singleton`, `@inject`, `@Mapper`, `@get`, `@post` |
| `water` | Classes | `DoughFactory`, `Scope`, `Configuration`, `Service`, `Struct` |
| `egg` | Methods | `Builder`, `LoopMethod` |
| `sugar` | Other | `container`, `chat_model`, `redis_client` |
| `_class_registry` | User-defined Bean classes | `UserService`, `UserMapper` |

## Notes

- Embed plugin should be **declared last** in `pancake.xml` (`init_order=999` ensures other plugins register first)
- If two classes share the same name, the later one overrides the earlier one
- All subsequently registered decorators and Dough subclasses also auto-inject into builtins

---

[← Previous](05-plugin-system.md) | [Next →](07-mybatis.md)
