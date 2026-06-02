# Pancake Framework

> A decorator-driven Python web framework with IoC, MyBatis-style ORM, and AI workflow integration.

[中文文档](./README_CN.md)

## Features

- **Decorator-Driven** - Register services, controllers, and mappers with simple decorators
- **CLI Tool** - `pancake create/run/check/build` commands for project management
- **Auto Dependency Injection** - `@auto_inject()` automatically resolves parameters from YAML/JSON config
- **MyBatis Plus ORM** - Async ORM with `BaseMapper` CRUD, `@Select`/`@Insert` SQL annotations, dynamic SQL
- **FastAPI Web Server** - Built-in `@get_controller`/`@post_controller` decorators
- **IoC Container** - Singleton, transient, and scoped dependency management
- **LangGraph Integration** - AI workflow nodes, edges, and state graphs
- **Message Queue** - In-memory `SimpleBroker` and `RedisBroker` for event-driven architecture
- **Plugin System** - XML-managed plugin loading with init-order control
- **Centralized Settings** - All paths and configs managed through `settings.py`, fully user-customizable

## Quick Start

### Install

```bash
pip install pancake
```

### Create a Project

```bash
pancake create myapp
cd myapp
```

### Run

```bash
# Using CLI
pancake run

# Or using Python
python main.py
```

The server starts at `http://127.0.0.1:8080` by default.

### CLI Commands

| Command | Description |
|---------|-------------|
| `pancake create <name>` | Create a new project with standard structure |
| `pancake run` | Run the project |
| `pancake check` | Check project structure and environment |
| `pancake build` | Package project as wheel |

### Project Structure

After `pancake create myapp`:

```
myapp/
├── main.py              # Entry point: import pancake; pancake.run()
├── pancake.xml          # Plugin & config management
├── pyproject.toml       # Dependencies
└── src/
    ├── resource/
    │   ├── yaml/        # YAML config files
    │   └── db/          # SQLite database
    ├── mapper/          # Data access layer
    └── controller/      # Web controllers
```

## Usage

### Web Controller

```python
@get_controller("/hello")
def hello():
    return {"message": "Hello from Pancake!"}

@post_controller("/users")
async def create_user(name: str, age: int, email: str):
    return {"id": await UserMapper().insert(name=name, age=age, email=email)}
```

### MyBatis Plus ORM

```python
@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        age: int = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...
```

Built-in CRUD: `select_by_id`, `select_list`, `select_one`, `select_count`, `insert`, `insert_batch`, `update_by_id`, `delete_by_id`.

Chain queries:

```python
from pancake.ovenware.mybatis.wrapper import qw, uw

users = await mapper.select(qw().ge("age", 18).like("name", "%Ali%").orderByDesc("age").limit(50))
await mapper.update(uw().set("name", "Bob").eq("id", 1))
await mapper.delete(qw().lt("age", 18))
```

### Auto Dependency Injection

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

get_config()  # {"title": "My App", "port": 8080}
```

### IoC Container

```python
container.register(UserService, UserService, Scope.SINGLETON)
service = container.resolve(UserService)
```

### Event-Driven Messaging

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}

@on_event("order.created")
async def notify_inventory(message):
    print(f"Order received: {message}")
```

### Lifecycle Hooks

```python
class MyService(Lifecycle):
    async def on_init(self):
        self.cache = {}

    async def on_start(self):
        await self.load_data()

    async def on_stop(self):
        await self.cleanup()
```

## Configuration

### XML Startup Config (`pancake.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
  <global>
    <service.title>My App</service.title>
    <service.version>1.0.0</service.version>
    <service.host>0.0.0.0</service.host>
    <service.port>3000</service.port>
    <paths.yaml_dir>config/yml</paths.yaml_dir>
  </global>
  <plugins>
    <plugin name="embed" init-order="0"/>
    <plugin name="mybatis" init-order="1"/>
    <plugin name="web" init-order="2"/>
    <plugin name="langgraph" enabled="false"/>
  </plugins>
</pancake>
```

- **`<global>`**: Config values merged into YAML config (XML takes priority)
- **`<plugin name="...">`**: `source` auto-derived as `ovenware.<name>` if omitted
- **`init-order`**: Lower loads first (default: 0)
- **`enabled="false"`**: Skip plugin init but still load decorators
- **`${env:VAR_NAME}`**: Resolved from environment variables

### Path Configuration

All paths are configurable via `pancake.xml` or YAML:

| Key | Default | Description |
|-----|---------|-------------|
| `paths.src_dir` | `src` | User code root |
| `paths.yaml_dir` | `src/resource/yaml` | YAML config directory |
| `paths.json_dir` | `src/resource/json` | JSON config directory |
| `paths.mapper_dir` | `src/mapper` | Mapper directory |
| `paths.controller_dir` | `src/controller` | Controller directory |
| `paths.db_dir` | `src/resource/db` | Database directory |

### Service & Database Config

| Key | Default | Description |
|-----|---------|-------------|
| `service.title` | `Pancake App` | App name |
| `service.version` | `1.0.0` | App version |
| `service.host` | `127.0.0.1` | Bind host |
| `service.port` | `8080` | Bind port |
| `mybatis.database.url` | `sqlite:///...` | Database URL |
| `mybatis.database.min_size` | `1` | Connection pool min |
| `mybatis.database.max_size` | `5` | Connection pool max |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LOG_FILE` | Log file path |
| `EXTERNAL_PLUGIN_DIRS` | External plugin paths (`;` or `:` separated) |
| `PANCAKE_AUTO_INSTALL` | Auto-install missing dependencies |

## Optional Dependencies

```bash
pip install pancake[langgraph]   # LangGraph AI workflow
pip install pancake[grpc]        # gRPC remote calls
pip install pancake[redis]       # Redis message queue
pip install pancake[all]         # All optional deps
```

## Running Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## License

MIT
