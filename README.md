# Pancake Framework

> A decorator-driven Python web framework with IoC, MyBatis-style ORM, and AI workflow integration.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/pancake_framework?style=flat-square&color=blue)
![CI](https://img.shields.io/github/actions/workflow/status/Drayee/PancakeFramework/ci.yml?style=flat-square&label=CI)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat-square&logo=fastapi&logoColor=white)

</div>

[中文文档](./README_CN.md)

## Features

- **Zero Import** — All decorators and services auto-injected into builtins
- **Decorator-Driven** — Register controllers, mappers, services with simple decorators
- **CLI Tool** — `pancake create/run/check/build/plugin/config/audit`
- **MyBatis Plus ORM** — Async ORM with CRUD, `@Select`/`@Insert`, dynamic SQL, chain queries
- **FastAPI Web** — Controllers, filter chain (Spring Security-style), auth, middleware, WebSocket
- **IoC Container** — Singleton, transient, scoped dependency injection
- **AI Module** — Unified LLM client (OpenAI/DeepSeek/Gemini/Ollama), memory, RAG
- **Redis Cache** — `@cached` with anti-penetration/avalanche/breakdown protection
- **Message Queue** — Event-driven with SimpleBroker and RedisBroker
- **Remote Calls** — HTTP and gRPC via `@remote_node`
- **Lifecycle** — Init/start/stop/error hooks for components
- **Plugin System** — Auto-discovery, init-order control, external plugin dirs

## Quick Start

```bash
pip install pancake_framework
pancake create myapp && cd myapp
pancake run
```

Server starts at `http://127.0.0.1:8080`. Health check at `/health`.

### Minimal Example

```python
# No imports needed — everything is in builtins

@get_controller("/hello")
def hello():
    return {"message": "Hello from Pancake!"}

@Mapper
class UserMapper(BaseMapper):
    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...
```

## Documentation

| Module | Description |
|--------|-------------|
| [CLI](docs/cli.md) | Command-line tools |
| [Web](docs/web.md) | Controllers, filter chain, auth, middleware, WebSocket |
| [MyBatis ORM](docs/mybatis.md) | Mappers, CRUD, chain queries, dynamic SQL |
| [AI](docs/ai.md) | LLM client, memory, RAG |
| [Redis](docs/redis.md) | Cache, data structures, distributed locks |
| [IoC & DI](docs/ioc.md) | IoC container, `@auto_inject`, `@inject` |
| [Config](docs/config.md) | YAML/XML/env configuration |
| [Plugins](docs/plugin.md) | Plugin system and built-in plugins |
| [Lifecycle](docs/lifecycle.md) | Component lifecycle hooks |
| [Messaging](docs/messaging.md) | Event-driven message queue |
| [Remote](docs/remote.md) | HTTP and gRPC remote calls |

## Optional Dependencies

```bash
pip install pancake_framework[ai]          # AI module
pip install pancake_framework[langgraph]   # LangGraph workflow
pip install pancake_framework[redis]       # Redis cache & messaging
pip install pancake_framework[grpc]        # gRPC remote calls
pip install pancake_framework[cui]         # Click CLI commands
pip install pancake_framework[gui]         # Flet GUI
pip install pancake_framework[all]         # All optional deps
```

## Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## License

MIT
