# MyBatis Plus ORM

Async ORM inspired by MyBatis Plus. All decorators are auto-injected — no import needed.

## Entity Definition

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

### Built-in CRUD

`BaseMapper` provides these methods automatically:

| Method | Description |
|--------|-------------|
| `select_by_id(id)` | Get by primary key |
| `select_list(**kwargs)` | List with optional filters |
| `select_one(**kwargs)` | Get single record |
| `select_count(**kwargs)` | Count records |
| `insert(**kwargs)` | Insert a record |
| `insert_batch(entities)` | Batch insert |
| `update_by_id(id, **kwargs)` | Update by primary key |
| `delete_by_id(id)` | Delete by primary key |

## Chain Queries

```python
from pancake.ovenware.mybatis import qw, uw

# Query
users = await mapper.select(
    qw().ge("age", 18)
        .like("name", "%Ali%")
        .order_by_desc("age")
        .limit(50)
)

# Update
await mapper.update(uw().set("name", "Bob").eq("id", 1))

# Delete
await mapper.delete(qw().lt("age", 18))
```

### QueryWrapper Methods

| Method | Description |
|--------|-------------|
| `.eq(col, val)` | Equal |
| `.ne(col, val)` | Not equal |
| `.gt(col, val)` | Greater than |
| `.ge(col, val)` | Greater or equal |
| `.lt(col, val)` | Less than |
| `.le(col, val)` | Less or equal |
| `.like(col, val)` | LIKE |
| `.in(col, values)` | IN |
| `.between(col, a, b)` | BETWEEN |
| `.is_null(col)` | IS NULL |
| `.is_not_null(col)` | IS NOT NULL |
| `.order_by_asc(col)` | ORDER BY ASC |
| `.order_by_desc(col)` | ORDER BY DESC |
| `.limit(n)` | LIMIT |
| `.offset(n)` | OFFSET |

## Dynamic SQL

```xml-like syntax in @Select annotations:

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

## Configuration

```yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db    # or postgresql://... or mysql://...
    min_size: 1
    max_size: 5
```

## Database Dialects

Auto-detected from URL:
- **SQLite** — `sqlite:///path/to/db`
- **PostgreSQL** — `postgresql://user:pass@host:port/db`
- **MySQL** — `mysql://user:pass@host:port/db`

Type mappings are handled automatically.
