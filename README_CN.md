# Pancake Framework

> 一个装饰器驱动的 Python Web 框架，集成 IoC、MyBatis 风格 ORM 和 AI 工作流。

[English](./README.md)

## 特性

- **零 import** - 所有装饰器和服务自动注入 builtins，无需显式 import
- **装饰器驱动** - 用简单装饰器注册服务、控制器和 Mapper
- **CLI 命令行工具** - `pancake create/run/check/build` 管理项目
- **自动依赖注入** - `@auto_inject()` 自动从 YAML/JSON 配置解析参数
- **IoC 容器** - 支持单例、瞬态和作用域的依赖管理
- **MyBatis Plus ORM** - 异步 ORM，内置 `BaseMapper` CRUD、`@Select`/`@Insert` SQL 注解、动态 SQL、链式查询
- **多数据库支持** - SQLite / PostgreSQL / MySQL，自动检测
- **FastAPI Web 服务** - 内置 `@get_controller`/`@post_controller` 及全部 HTTP 方法
- **认证与授权** - `@auth_required`、`@role_required`，可插拔认证处理器
- **中间件与校验** - `@middleware`、`@validate`、`@transaction` 装饰器
- **AI 模块** - 统一 LLM 客户端 (OpenAI/DeepSeek/Gemini/Ollama)，短期 & 长期记忆，RAG
- **LangGraph 集成** - AI 工作流节点、边和状态图
- **Redis 缓存** - `@cached` 装饰器，防穿透/雪崩/击穿保护
- **消息队列** - 内存 `SimpleBroker` 和 `RedisBroker` 事件驱动架构
- **远程调用** - `@remote_node` 支持 HTTP 和 gRPC 远程调用
- **生命周期管理** - `Lifecycle` 基类，支持 init/start/stop/error 钩子
- **CUI** - Click CLI 命令注册，`@cui_command` 装饰器
- **GUI** - Flet (Flutter) GUI 页面注册，`@gui_page` 装饰器
- **插件系统** - 自动发现加载，init_order 控制顺序，支持外部插件目录
- **集中配置管理** - `settings.py` 统一管理路径和配置

## 快速开始

### 安装

```bash
pip install pancake_framework
```

### 创建项目

```bash
pancake create myapp
cd myapp
```

### 运行

```bash
# 使用 CLI
pancake run

# 或使用 Python
python main.py
```

服务默认启动在 `http://127.0.0.1:8080`，健康检查 `/health`。

### CLI 命令

| 命令 | 说明 |
|------|------|
| `pancake create <名称>` | 创建新项目，生成标准目录结构 |
| `pancake run` | 运行项目 |
| `pancake check` | 检查项目结构和环境 |
| `pancake build` | 打包项目为 wheel |

## 使用方法

### Web 控制器 (无需 import)

```python
@get_controller("/hello")
def hello():
    return {"message": "Hello from Pancake!"}

@post_controller("/users")
async def create_user(name: str, age: int):
    return {"id": await UserMapper().insert(name=name, age=age)}
```

### 认证与授权

```python
@set_auth_handler
async def authenticate(request, token):
    user = await verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

@get_controller("/profile")
@auth_required
async def get_profile(current_user):
    return {"user": current_user}

@delete_controller("/admin/users/{user_id}")
@role_required("admin")
async def delete_user(user_id: int):
    await UserMapper().delete_by_id(user_id)
```

### 中间件与事务

```python
@middleware(order=1)
async def log_request(request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} {time.time()-start:.3f}s")
    return response

@post_controller("/transfer")
@transaction
async def transfer(from_id: int, to_id: int, amount: float):
    # 该函数内的所有数据库操作在同一事务中执行
    ...
```

### MyBatis Plus ORM (无需 import)

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

内置 CRUD：`select_by_id`、`select_list`、`select_one`、`select_count`、`insert`、`insert_batch`、`update_by_id`、`delete_by_id`。

链式查询：

```python
users = await mapper.select(qw().ge("age", 18).like("name", "%Ali%").order_by_desc("age").limit(50))
await mapper.update(uw().set("name", "Bob").eq("id", 1))
await mapper.delete(qw().lt("age", 18))
```

### AI 模块 (无需 import)

配置 `src/resource/yaml/ai.yaml`，然后直接使用：

```python
# 对话
response = await chat_model.chat([{"role": "user", "content": "你好"}])

# 流式输出
async for chunk in chat_model.chat_stream([...]):
    print(chunk, end="")

# 短期记忆（对话上下文）
await short_term_memory.add("session_001", "user", "我叫小明")
messages = await short_term_memory.get_messages("session_001")

# 长期记忆（持久化存储）
await long_term_memory.remember("user_name", "小明")
name = await long_term_memory.recall("user_name")

# RAG 问答
await rag.add_document("Pancake 是一个 Python 框架...")
answer = await rag.ask("什么是 Pancake？")
```

支持的模型提供商：OpenAI、DeepSeek、Gemini、Ollama、智谱 GLM、Moonshot、Qwen、vLLM。

### Redis 缓存

```python
@cached(ttl=300)
async def get_user(user_id: int):
    return await db.query(user_id)

# CacheGuard 防穿透/雪崩/击穿
guard = CacheGuard(redis_client)
user = await guard.get_or_load("user:123", lambda: db.query(123), ttl=600, jitter=60)
```

### 事件驱动消息

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}

@on_event("order.created")
async def notify_inventory(message):
    print(f"收到订单: {message}")
```

### 生命周期钩子

```python
class MyService(Lifecycle):
    async def on_init(self):
        self.cache = {}

    async def on_start(self):
        await self.load_data()

    async def on_stop(self):
        await self.cleanup()
```

### CUI (CLI 命令)

```python
@cui_command("greet", help="Say hello")
@cui_option("--name", "-n", default="World", help="Name")
def greet(name: str):
    click.echo(f"Hello, {name}!")
```

### GUI (Flet/Flutter)

```python
@gui_page("/", title="Home")
def home(page: ft.Page):
    page.add(ft.Text("Welcome to Pancake GUI"))
```

## 可选依赖

```bash
pip install pancake_framework[ai]          # AI 模块 (OpenAI, Gemini 等)
pip install pancake_framework[langgraph]   # LangGraph AI 工作流
pip install pancake_framework[redis]       # Redis 缓存和消息队列
pip install pancake_framework[grpc]        # gRPC 远程调用
pip install pancake_framework[cui]         # Click CLI 命令
pip install pancake_framework[gui]         # Flet GUI
pip install pancake_framework[all]         # 全部可选依赖
```

## TODO

- [ ] 数据库迁移支持
- [ ] 配置热重载
- [ ] 分页 `Page` 对象抽象
- [ ] OpenTelemetry / 指标集成
- [ ] 优雅停机 (信号处理)
- [ ] WebSocket 支持
- [ ] 限流中间件
- [ ] API 文档自动生成
- [ ] 更多数据库方言 (SQLite/PG/MySQL 类型映射)
- [ ] 连接池健康检查和自动重连

## 运行测试

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 开源协议

MIT
