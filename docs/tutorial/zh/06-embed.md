# 6. Embed 插件 — 零 import

[← 上一节](05-plugin-system.md) | [下一节 →](07-mybatis.md)

---

## 概述

`pancake-embed` 是 Pancake 最重要的插件之一，它实现了"零 import"机制。启用后，所有框架装饰器、基类和服务自动注入 Python 的 `builtins` 模块，用户代码无需任何 `import` 语句。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>embed</artifactId>
</dependency>
```

## 原理

Embed 插件在 `init_order=999`（最后）加载：

1. 扫描 `registry.flour`（装饰器）、`water`（类）、`egg`（方法）、`sugar`（其他）
2. 将所有已注册的名称注入 `builtins`
3. Patch `DoughMeta` 元类，后续定义的 Dough 子类自动注入
4. Patch `register_decorator`，后续注册的装饰器自动注入

## 效果

启用前（需要 import）：

```python
from pancake import Service, singleton, inject
from pancake_mybatis import Mapper, BaseMapper, Select

@singleton
class UserService(Service):
    pass
```

启用后（无需 import）：

```python
@singleton
class UserService(Service):
    pass

@Mapper
class UserMapper(BaseMapper):
    @Select("SELECT * FROM users")
    async def find_all(self): ...
```

## 注入的内容

| 来源 | 内容 | 示例 |
|------|------|------|
| `flour` | 装饰器 | `@singleton`, `@inject`, `@Mapper`, `@get`, `@post` |
| `water` | 类 | `DoughFactory`, `Scope`, `Configuration`, `Service`, `Struct` |
| `egg` | 方法 | `Builder`, `LoopMethod` |
| `sugar` | 其他 | `container`, `chat_model`, `redis_client` |
| `_class_registry` | 用户定义的 Bean 类 | `UserService`, `UserMapper` |

## 注意事项

- Embed 插件应该在 `pancake.xml` 中**最后声明**（`init_order=999` 确保其他插件先注册）
- 如果两个类同名，后定义的会覆盖先定义的
- 所有后续注册的装饰器和 Dough 子类也会自动注入 builtins

---

[← 上一节](05-plugin-system.md) | [下一节 →](07-mybatis.md)
