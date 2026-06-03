# Pancake Framework

> 一个装饰器驱动的 Python Web 框架，集成 IoC、MyBatis 风格 ORM 和 AI 工作流。

[English](./README.md)

## 特性

- **零 import** — 所有装饰器和服务自动注入 builtins，无需显式 import
- **装饰器驱动** — 用简单装饰器注册控制器、Mapper、服务
- **CLI 工具** — `pancake create/run/check/build/plugin/config/audit`
- **MyBatis Plus ORM** — 异步 ORM，内置 CRUD、`@Select`/`@Insert`、动态 SQL、链式查询
- **FastAPI Web** — 控制器、过滤器链（类 Spring Security）、认证、中间件、WebSocket
- **IoC 容器** — 单例、瞬态、作用域依赖注入
- **AI 模块** — 统一 LLM 客户端 (OpenAI/DeepSeek/Gemini/Ollama)、记忆、RAG
- **Redis 缓存** — `@cached` 装饰器，防穿透/雪崩/击穿保护
- **消息队列** — 事件驱动，支持 SimpleBroker 和 RedisBroker
- **远程调用** — 通过 `@remote_node` 支持 HTTP 和 gRPC
- **生命周期** — 组件 init/start/stop/error 钩子
- **插件系统** — 自动发现加载，init_order 控制顺序，支持外部插件目录

## 快速开始

```bash
pip install pancake_framework
pancake create myapp && cd myapp
pancake run
```

服务启动在 `http://127.0.0.1:8080`，健康检查 `/health`。

### 最小示例

```python
# 无需 import — 所有功能已注入 builtins

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

## 文档

| 模块 | 说明 |
|------|------|
| [CLI](docs/cn/cli.md) | 命令行工具 |
| [Web](docs/cn/web.md) | 控制器、过滤器链、认证、中间件、WebSocket |
| [MyBatis ORM](docs/cn/mybatis.md) | Mapper、CRUD、链式查询、动态 SQL |
| [AI](docs/cn/ai.md) | LLM 客户端、记忆、RAG |
| [Redis](docs/cn/redis.md) | 缓存、数据结构、分布式锁 |
| [IoC & DI](docs/cn/ioc.md) | IoC 容器、`@auto_inject`、`@inject` |
| [配置](docs/cn/config.md) | YAML/XML/环境变量配置 |
| [插件](docs/cn/plugin.md) | 插件系统和内置插件 |
| [生命周期](docs/cn/lifecycle.md) | 组件生命周期钩子 |
| [消息队列](docs/cn/messaging.md) | 事件驱动消息队列 |
| [远程调用](docs/cn/remote.md) | HTTP 和 gRPC 远程调用 |

## 可选依赖

```bash
pip install pancake_framework[ai]          # AI 模块
pip install pancake_framework[langgraph]   # LangGraph 工作流
pip install pancake_framework[redis]       # Redis 缓存和消息队列
pip install pancake_framework[grpc]        # gRPC 远程调用
pip install pancake_framework[cui]         # Click CLI 命令
pip install pancake_framework[gui]         # Flet GUI
pip install pancake_framework[all]         # 全部可选依赖
```

## 测试

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 开源协议

MIT
