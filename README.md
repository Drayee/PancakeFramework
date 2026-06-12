# Pancake Framework

> A decorator-driven Python framework with Spring-inspired IoC, MyBatis Plus ORM, AI workflow, and a plugin system.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/pancake_framework?style=flat-square&color=blue)

</div>

[English](./README.md) | [中文文档](./README_CN.md)

## Features

- **Dough IoC Container** — Spring-style Bean management with full lifecycle: `on_init` → `on_start` → `on_stop` → `on_destroy`
- **Decorator-Driven** — `@singleton`, `@prototype`, `@lazy`, `@inject`, `@config`, `@depends_on`
- **Async First** — All lifecycle methods support `async def`; DoughFactory handles sync/async transparently
- **Zero Import** — The `pancake-embed` plugin injects all decorators and classes into `builtins`
- **Base Classes** — `Configuration` (bean factory), `Service`, `Struct` (dataclass + Dough), `Function`
- **MyBatis Plus ORM** — `@Mapper`, `@Select`/`@Insert`/`@Update`/`@Delete`, chain queries `qw()`, dynamic SQL, pagination
- **aiohttp Web Server** — `@controller`, `@get`/`@post`, parameter binding, middleware, exception handling, CORS
- **Jinja2 Templates** — `@template` decorator for automatic HTML rendering
- **Spring Security-Style** — Authentication/authorization, JWT, CSRF, rate limiting, security headers
- **AI Module** — Unified LLM client (OpenAI/DeepSeek/Gemini/Ollama), short/long-term memory, RAG
- **Redis Cache** — `@cached` decorator, CacheGuard (anti-penetration/avalanche/breakdown)
- **Message Queue** — `@event_node`/`@on_event` event-driven, SimpleBroker/RedisBroker
- **Remote Calls** — `HttpRemote`/`GrpcRemote` HTTP and gRPC clients
- **LangGraph Workflow** — `@langgraph_node`/`@langgraph_edge` state graph orchestration
- **GUI/CUI** — Flet desktop GUI and Click CLI framework integration
- **Plugin System** — XML declarative management, auto pip install, `pancake plugin` CLI

## Quick Start

### Install

```bash
pip install pancake_framework
```

### Create Project

```bash
pancake create myapp
cd myapp
```

### Run

```bash
python main.py
# or
pancake run
```

### Project Structure

```
myapp/
├── main.py                  # Entry point
├── pancake.xml              # Plugin and global config
├── pyproject.toml           # Project metadata
└── src/
    ├── resource/
    │   ├── yaml/            # YAML config
    │   │   └── service.yaml
    │   └── json/            # JSON config
    └── templates/           # HTML templates
```

## Core Concepts

### Dough IoC System

The core of Pancake is the **Dough** system — a Spring-style IoC container. All Beans extend the `Dough` base class and are managed by `DoughFactory`.

#### Bean Lifecycle

```
__init__()  →  on_init()  →  on_start()  →  [running]  →  on_stop()  →  on_destroy()
   construct    @PostConstruct    ready                        stop         @PreDestroy
```

#### Scopes

| Scope | Decorator | Description |
|-------|-----------|-------------|
| Singleton | `@singleton` | One instance per factory (default) |
| Prototype | `@prototype` | New instance every resolve |
| Lazy | `@lazy` | Created on first access |

#### Base Classes

| Base | Purpose |
|------|---------|
| `Service` | Service class, method collection |
| `Configuration` | Config class, non-private method return values auto-register as Beans |
| `Struct` | Data structure, inherits dataclass, for DTOs/forms |
| `Function` | Function wrapper, provides `call()` method |

### Zero Import

With the `pancake-embed` plugin enabled, all decorators and classes are auto-injected into `builtins`:

```python
# No imports needed
@singleton
@depends_on("DatabaseService")
class UserService(Service):
    async def on_init(self):
        self.db = DoughFactory.get().resolve("DatabaseService")

    async def find_user(self, user_id: int):
        return await self.db.query(user_id)
```

### Decorators

| Decorator | Target | Description |
|-----------|--------|-------------|
| `@dough` | Class | Mark class as Bean |
| `@singleton` | Class | Singleton scope |
| `@prototype` | Class | Prototype scope |
| `@lazy` | Class | Lazy initialization |
| `@service` | Class | Convert to Service subclass |
| `@configuration` | Class | Convert to Configuration subclass |
| `@struct` | Class | Mark as data structure (dataclass) |
| `@function` | Function | Convert to Function subclass |
| `@inject` | Class/Function | Auto-inject dependencies by type |
| `@inject_name` | Class/Function | Auto-inject dependencies by name |
| `@config` | Class | Inject Struct fields from settings |
| `@depends_on("A", "B")` | Class | Declare Bean dependencies |
| `@import_class(Cls)` | Class | Auto-register external classes |
| `@maker` | Method | Mark method return value as Bean |
| `@no_maker` | Method | Exclude method from auto-registration |

## Plugin System

Pancake uses a plugin architecture. All extensions are provided as plugins, declared in `pancake.xml` `<dependencies>`.

### Plugins

| Plugin | Package | Description |
|--------|---------|-------------|
| **embed** | `pancake-embed` | Zero import, inject into builtins |
| **mybatis** | `pancake-mybatis` | MyBatis Plus ORM |
| **web** | `pancake-web` | aiohttp Web server |
| **web-template** | `pancake-web-template` | Jinja2 template rendering |
| **web-security** | `pancake-web-security` | Spring Security-style security |
| **ai** | `pancake-ai` | AI model integration |
| **redis** | `pancake-redis` | Redis cache |
| **langgraph** | `pancake-langgraph` | LangGraph workflow |
| **remote** | `pancake-remote` | HTTP/gRPC remote calls |
| **cui** | `pancake-cui` | Click CLI framework |
| **gui** | `pancake-gui` | Flet desktop GUI |

### Plugin Management

```bash
pancake plugin list              # List configured plugins
pancake plugin add <name>        # Add plugin to pancake.xml
pancake plugin remove <name>     # Remove plugin
pancake plugin clear             # Clear all plugins
```

### pancake.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <config>
        <service.title>myapp</service.title>
        <service.port>8080</service.port>
    </config>
    <dependencies>
        <dependency>
            <groupId>io.pancake</groupId>
            <artifactId>embed</artifactId>
        </dependency>
        <dependency>
            <groupId>io.pancake</groupId>
            <artifactId>mybatis</artifactId>
        </dependency>
        <dependency>
            <groupId>io.pancake</groupId>
            <artifactId>web</artifactId>
        </dependency>
    </dependencies>
</pancake>
```

## Documentation

| Module                                                     | Description                                              |
|------------------------------------------------------------|----------------------------------------------------------|
| [Framework Tutorial (English)](docs/tutorial/en/README.md) | Complete tutorial covering core concepts and all plugins |
| [框架教程 (中文)](docs/tutorial/zh/README.md)                    | 完整教程，涵盖核心概念和所有插件                                         |

## Optional Dependencies

```bash
pip install pancake_framework[ai]          # AI module (openai)
pip install pancake_framework[redis]       # Redis cache
pip install pancake_framework[sqlite]      # SQLite database
pip install pancake_framework[postgres]    # PostgreSQL database
pip install pancake_framework[mysql]       # MySQL database
pip install pancake_framework[langgraph]   # LangGraph workflow
pip install pancake_framework[grpc]        # gRPC remote calls
pip install pancake_framework[gui]         # Flet GUI
pip install pancake_framework[all]         # All optional deps
```

## Architecture

```
pancake/                    # Framework core
├── __init__.py             # Entry: init() → run()
├── run.py                  # Pipeline: load_xml → load_config → load_ovenware → load_dish → build
├── dough.py                # Dough base, Scope enum, DoughMeta metaclass
├── registry.py             # Global registry: flour/water/egg/sugar
├── decorators/             # Decorators: scope/bean/inject/config/convert
├── settings.py             # Centralized config management
├── base/                   # Base classes: Configuration, Service, Struct, Function
├── factory/                # DoughFactory + PackageManager
├── builder/                # Build pipeline: load_dlc(plugins) + load_src(user code) + build
├── cli/                    # CLI: init/create/run/check/build/plugin/config/audit
├── ovenware/               # Plugin base InitAction + Broker messaging
├── resource/               # Config loaders: YAML/JSON/XML + logging + hot reload
└── tool/                   # Utilities: ProgressBar
```

## CLI Commands

```bash
pancake version              # Show version
pancake init                 # Initialize project in current directory
pancake create <name>        # Create new project
pancake run                  # Run project
pancake check                # Check project structure and environment
pancake build                # Build project as wheel
pancake config show          # Show current config
pancake audit                # Audit code quality
pancake update               # Update framework
pancake install              # Install missing dependencies
```

## Startup Flow

```
main.py → pancake.run()
  ├── init()                    # Environment check, structure check, load dotenv/logging
  └── run.py → run()
      ├── load_xml()            # Load pancake.xml → plugin list + global config
      ├── load_config()         # Load YAML/JSON → settings
      ├── load_ovenware()       # Load plugins (sorted by init_order)
      ├── load_dish()           # Load user code from src/
      ├── build()               # Create Beans → topological sort → on_init → on_start
      └── run_loop_methods()    # Run loop_method (e.g., Web server)
```

## Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## License

MIT
