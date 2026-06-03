# Plugin System

Pancake auto-discovers and loads plugins from the `ovenware/` directory. Each plugin is a `.py` file or package with a `Main` class.

## Plugin Structure

```python
# pancake/ovenware/my_plugin.py
from pancake.ovenware import InitAction

class Main(InitAction):
    init_order = 10       # Load order (lower = earlier)
    _dependencies = []    # pip packages required
    _extras = "my_extra"  # extras_require group

    def __init__(self):
        # Initialization logic
        pass

    @staticmethod
    def check():
        # Check dependencies
        check_dependencies(Main._dependencies, Main._extras)

    def build(self):
        # Post-initialization build step
        pass

    def loop_method(self):
        # Runs after server starts
        pass
```

## Init Order

Controls plugin loading sequence. Lower values load first.

| Plugin | init_order |
|--------|------------|
| `embed` | -10 (last, injects builtins) |
| `mybatis` | 1 |
| `redis_cache` | 2 |
| `ai_model` | 4 |
| `web` | 50 |

## External Plugins

Set `EXTERNAL_PLUGIN_DIRS` environment variable to load plugins from custom directories:

```bash
export EXTERNAL_PLUGIN_DIRS="/path/to/plugins"
```

## Disabling Plugins

Disable built-in plugins via YAML:

```yaml
framework:
  disable_dlc:
    - langgraph
    - external_plugin
```

Or via `pancake.xml`:

```xml
<plugins>
    <plugin name="langgraph" enabled="false"/>
</plugins>
```

## CLI Plugin Management

```bash
# List all plugins and status
pancake plugin list

# Add a plugin to pancake.xml
pancake plugin add my_plugin
```

## Registration

Plugins register decorators, classes, and instances to the `oven` registry:

```python
from pancake import oven

# Decorators (auto-injected into builtins)
oven.muffin_flour["my_decorator"] = my_decorator

# Classes
oven.muffin_water["MyClass"] = MyClass

# Instances / factories
oven.muffin_sugar["my_service"] = get_my_service

# Config values
oven.pancake_yaml["custom.key"] = "value"
```

## Built-in Plugins

| Plugin | Description |
|--------|-------------|
| `embed` | Injects all registered items into builtins |
| `mybatis` | ORM with mapper, SQL parsing, connection management |
| `web` | FastAPI web server, controllers, filters, auth |
| `redis_cache` | Redis client, cache protection, `@cached` |
| `ai_model` | LLM client, memory, RAG |
| `broker` | Message queue (SimpleBroker / RedisBroker) |
| `lifecycle` | Lifecycle hooks (init/start/stop/error) |
| `remote` | HTTP and gRPC remote calls |
| `langgraph` | AI workflow nodes and edges |
| `external_plugin` | External plugin loader |
