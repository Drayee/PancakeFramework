# 7. MyBatis 插件 — ORM

[← 上一节](06-embed.md) | [下一节 →](08-web.md)

---

## 概述

`pancake-mybatis` 提供 MyBatis Plus 风格的异步 ORM，支持 SQLite、PostgreSQL、MySQL。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>mybatis</artifactId>
</dependency>
```

## 配置

```yaml
# src/resource/yaml/mybatis.yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db
    min_size: 1
    max_size: 5
```

| 数据库 | URL 格式 |
|--------|----------|
| SQLite | `sqlite:///resource/db/app.db` |
| PostgreSQL | `postgresql://user:pass@host/db` |
| MySQL | `mysql://user:pass@host/db` |

## 定义 Mapper

```python
@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        email: str = None
        age: int = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users")
    async def find_all(self) -> list[User]: ...

    @Select("SELECT * FROM users WHERE id = #{id}")
    async def find_by_id(self, id: int) -> User: ...

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...

    @Insert("INSERT INTO users (name, email, age) VALUES (#{name}, #{email}, #{age})")
    async def insert_user(self, name: str, email: str, age: int) -> int: ...

    @Update("UPDATE users SET name = #{name} WHERE id = #{id}")
    async def update_name(self, id: int, name: str) -> int: ...

    @Delete("DELETE FROM users WHERE id = #{id}")
    async def delete_by_id(self, id: int) -> int: ...
```

## SQL 注解

| 注解 | 用途 |
|------|------|
| `@Select(sql)` | 查询多条 |
| `@SelectOne(sql)` | 查询单条 |
| `@Insert(sql)` | 插入记录 |
| `@Update(sql)` | 更新记录 |
| `@Delete(sql)` | 删除记录 |

SQL 参数使用 `#{param}` 占位符，自动转换为参数化查询（防注入）。

## 内置 CRUD 方法

`BaseMapper` 提供内置方法，无需手写 SQL：

```python
# 插入
await mapper.insert(User(name="Alice", email="alice@example.com", age=25))
await mapper.insert_batch([user1, user2, user3])

# 按 ID 操作
user = await mapper.select_by_id(1)
await mapper.update_by_id(User(id=1, name="Bob"))
await mapper.delete_by_id(1)

# 条件查询
users = await mapper.select_list(qw().eq("name", "Alice"))
count = await mapper.select_count(qw().gt("age", 18))
user = await mapper.select_one(qw().eq("email", "alice@example.com"))

# 分页
page = Page(page_num=1, page_size=10)
result = await mapper.select_page(page, qw().eq("status", "active"))
```

## 链式查询

### QueryWrapper — 查询条件

```python
from pancake_mybatis import qw

# 等值
qw().eq("name", "Alice")

# 不等
qw().ne("status", "deleted")

# 大于/小于
qw().gt("age", 18).lt("age", 60)
qw().ge("score", 60).le("score", 100)

# LIKE
qw().like("name", "Ali")        # %Ali%
qw().like_left("name", "ice")   # %ice
qw().like_right("name", "Ali")  # Ali%

# IN
qw().in("status", ["active", "pending"])

# IS NULL / IS NOT NULL
qw().is_null("deleted_at")
qw().is_not_null("email")

# 排序
qw().order_by_asc("name")
qw().order_by_desc("created_at")

# 分页
qw().limit(50).offset(0)

# 组合
qw().eq("status", "active")
    .ge("age", 18)
    .like("name", "A")
    .order_by_desc("age")
    .limit(50)
```

### UpdateWrapper — 更新条件

```python
from pancake_mybatis import uw

uw().set("name", "Bob").eq("id", 1)

# 多字段
uw().set("name", "Bob")
    .set("email", "bob@example.com")
    .eq("status", "active")
```

## 事务

### @Transactional 装饰器

```python
@Transactional
async def transfer_money(from_id: int, to_id: int, amount: int):
    await mapper.update(uw().set("balance", "balance - #{amount}").eq("id", from_id))
    await mapper.update(uw().set("balance", "balance + #{amount}").eq("id", to_id))
```

### 手动事务

```python
from pancake_mybatis import begin_transaction

async with begin_transaction() as tx:
    await mapper.insert_user("Alice", "alice@example.com", 25)
    await mapper.insert_user("Bob", "bob@example.com", 30)
    # 自动提交或回滚
```

## 分页

```python
from pancake_mybatis import Page

page = Page(page_num=1, page_size=10)
result = await mapper.select_page(page, qw().eq("status", "active"))

# result.records — 数据列表
# result.total   — 总记录数
# result.pages   — 总页数
# result.current — 当前页
# result.size    — 每页大小
```

## 自动建表

```python
@Table("users")
class User:
    @Column(primary_key=True, auto_increment=True)
    id: int = None

    @Column(nullable=False, length=50)
    name: str = None

    @Column(unique=True, length=100)
    email: str = None

    @Column(default=0)
    age: int = None
```

## 完整示例

```python
# src/mapper/user_mapper.py

@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        email: str = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...

# src/service/user_service.py

@singleton
@inject
class UserService(Service):
    user_mapper: UserMapper

    async def get_active_users(self):
        return await self.user_mapper.select_list(
            qw().eq("status", "active").order_by_desc("created_at")
        )

# src/controller/user_controller.py

@controller("/api/users")
@inject
class UserController:
    user_service: UserService

    @get("/")
    async def list_users(self, request):
        return await self.user_service.get_active_users()
```

---

[← 上一节](06-embed.md) | [下一节 →](08-web.md)
