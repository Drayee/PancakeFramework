# MyBatis Plus ORM

异步 ORM，灵感来自 MyBatis Plus。所有装饰器自动注入，无需 import。

## 实体定义

```python
@dataclass
class User:
    id: int = None
    name: str = None
    age: int = None
```

## Mapper

```python
@Mapper
class UserMapper(BaseMapper):
    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...

    @SelectOne("SELECT * FROM users WHERE id = #{id}")
    async def find_by_id(self, id: int) -> User: ...

    @Insert("INSERT INTO users (name, age) VALUES (#{name}, #{age})")
    async def add_user(self, name: str, age: int) -> int: ...

    @Update("UPDATE users SET name = #{name} WHERE id = #{id}")
    async def rename(self, id: int, name: str) -> int: ...

    @Delete("DELETE FROM users WHERE id = #{id}")
    async def remove(self, id: int) -> int: ...
```

### 内置 CRUD

`BaseMapper` 自动提供以下方法：

| 方法 | 说明 |
|------|------|
| `select_by_id(id)` | 按主键查询 |
| `select_list(**kwargs)` | 条件列表查询 |
| `select_one(**kwargs)` | 查询单条记录 |
| `select_count(**kwargs)` | 统计记录数 |
| `insert(**kwargs)` | 插入记录 |
| `insert_batch(entities)` | 批量插入 |
| `update_by_id(id, **kwargs)` | 按主键更新 |
| `delete_by_id(id)` | 按主键删除 |

## 链式查询

```python
from pancake.ovenware.mybatis import qw, uw

# 查询
users = await mapper.select(
    qw().ge("age", 18)
        .like("name", "%Ali%")
        .order_by_desc("age")
        .limit(50)
)

# 更新
await mapper.update(uw().set("name", "Bob").eq("id", 1))

# 删除
await mapper.delete(qw().lt("age", 18))
```

### QueryWrapper 方法

| 方法 | 说明 |
|------|------|
| `.eq(col, val)` | 等于 |
| `.ne(col, val)` | 不等于 |
| `.gt(col, val)` | 大于 |
| `.ge(col, val)` | 大于等于 |
| `.lt(col, val)` | 小于 |
| `.le(col, val)` | 小于等于 |
| `.like(col, val)` | LIKE |
| `.in(col, values)` | IN |
| `.between(col, a, b)` | BETWEEN |
| `.is_null(col)` | IS NULL |
| `.is_not_null(col)` | IS NOT NULL |
| `.order_by_asc(col)` | ORDER BY ASC |
| `.order_by_desc(col)` | ORDER BY DESC |
| `.limit(n)` | LIMIT |
| `.offset(n)` | OFFSET |

## 动态 SQL

```python
@Select("""
    SELECT * FROM users
    <where>
        <if test="name">AND name = #{name}</if>
        <if test="age">AND age = #{age}</if>
    </where>
    <choose>
        <when test="order == 'age'">ORDER BY age</when>
        <otherwise>ORDER BY id</otherwise>
    </choose>
""")
```

## 配置

```yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db    # 或 postgresql://... 或 mysql://...
    min_size: 1
    max_size: 5
```

## 数据库方言

根据 URL 自动检测：
- **SQLite** — `sqlite:///path/to/db`
- **PostgreSQL** — `postgresql://user:pass@host:port/db`
- **MySQL** — `mysql://user:pass@host:port/db`

类型映射自动处理。
