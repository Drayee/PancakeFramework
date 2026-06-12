# 7. MyBatis Plugin — ORM

[← Previous](06-embed.md) | [Next →](08-web.md)

---

## Overview

`pancake-mybatis` provides MyBatis Plus-style async ORM, supporting SQLite, PostgreSQL, and MySQL.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>mybatis</artifactId>
</dependency>
```

## Configuration

```yaml
# src/resource/yaml/mybatis.yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db
    min_size: 1
    max_size: 5
```

| Database | URL Format |
|----------|------------|
| SQLite | `sqlite:///resource/db/app.db` |
| PostgreSQL | `postgresql://user:pass@host/db` |
| MySQL | `mysql://user:pass@host/db` |

## Defining Mappers

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

## SQL Annotations

| Annotation | Purpose |
|------------|---------|
| `@Select(sql)` | Query multiple |
| `@SelectOne(sql)` | Query single |
| `@Insert(sql)` | Insert |
| `@Update(sql)` | Update |
| `@Delete(sql)` | Delete |

SQL parameters use `#{param}` placeholders, auto-converted to parameterized queries (injection-safe).

## Built-in CRUD Methods

`BaseMapper` provides built-in methods, no SQL needed:

```python
# Insert
await mapper.insert(User(name="Alice", email="alice@example.com", age=25))
await mapper.insert_batch([user1, user2, user3])

# By ID operations
user = await mapper.select_by_id(1)
await mapper.update_by_id(User(id=1, name="Bob"))
await mapper.delete_by_id(1)

# Conditional query
users = await mapper.select_list(qw().eq("name", "Alice"))
count = await mapper.select_count(qw().gt("age", 18))
user = await mapper.select_one(qw().eq("email", "alice@example.com"))

# Pagination
page = Page(page_num=1, page_size=10)
result = await mapper.select_page(page, qw().eq("status", "active"))
```

## Chain Queries

### QueryWrapper — Query Conditions

```python
from pancake_mybatis import qw

# Equals
qw().eq("name", "Alice")

# Not equals
qw().ne("status", "deleted")

# Greater/Less
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

# Order
qw().order_by_asc("name")
qw().order_by_desc("created_at")

# Limit
qw().limit(50).offset(0)

# Combine
qw().eq("status", "active")
    .ge("age", 18)
    .like("name", "A")
    .order_by_desc("age")
    .limit(50)
```

### UpdateWrapper — Update Conditions

```python
from pancake_mybatis import uw

uw().set("name", "Bob").eq("id", 1)

# Multiple fields
uw().set("name", "Bob")
    .set("email", "bob@example.com")
    .eq("status", "active")
```

## Transactions

### @Transactional Decorator

```python
@Transactional
async def transfer_money(from_id: int, to_id: int, amount: int):
    await mapper.update(uw().set("balance", "balance - #{amount}").eq("id", from_id))
    await mapper.update(uw().set("balance", "balance + #{amount}").eq("id", to_id))
```

### Manual Transaction

```python
from pancake_mybatis import begin_transaction

async with begin_transaction() as tx:
    await mapper.insert_user("Alice", "alice@example.com", 25)
    await mapper.insert_user("Bob", "bob@example.com", 30)
    # Auto-commit or rollback
```

## Pagination

```python
from pancake_mybatis import Page

page = Page(page_num=1, page_size=10)
result = await mapper.select_page(page, qw().eq("status", "active"))

# result.records — Data list
# result.total   — Total count
# result.pages   — Total pages
# result.current — Current page
# result.size    — Page size
```

## Auto Schema

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

## Complete Example

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

[← Previous](06-embed.md) | [Next →](08-web.md)
