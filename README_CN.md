# Pancake Framework

> 一个装饰器驱动的 Python Web 框架，集成 IoC、MyBatis 风格 ORM 和 AI 工作流。

[English](./README.md)

## 特性

- **装饰器驱动** - 用简单装饰器注册服务、控制器和 Mapper
- **CLI 命令行工具** - `pancake create/run/check/build` 管理项目
- **自动依赖注入** - `@auto_inject()` 自动从 YAML/JSON 配置解析参数
- **MyBatis Plus ORM** - 异步 ORM，内置 CRUD、SQL 注解、动态 SQL
- **FastAPI Web 服务** - 内置 `@get_controller`/`@post_controller` 装饰器
- **IoC 容器** - 支持单例、瞬态和作用域的依赖管理
- **LangGraph 集成** - AI 工作流节点、边和状态图
- **消息队列** - 内存 `SimpleBroker` 和 `RedisBroker` 事件驱动架构
- **插件系统** - XML 统一管理插件加载、顺序和配置
- **集中配置管理** - `settings.py` 统一管理路径和配置，支持用户自定义

## 快速开始

### 安装

```bash
pip install pancake
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

服务默认启动在 `http://127.0.0.1:8080`。

### CLI 命令

| 命令 | 说明 |
|------|------|
| `pancake create <名称>` | 创建新项目，生成标准目录结构 |
| `pancake run` | 运行项目 |
| `pancake check` | 检查项目结构和环境 |
| `pancake build` | 打包项目为 wheel |

### 项目结构

执行 `pancake create myapp` 后：

```
myapp/
├── main.py              # 入口：import pancake; pancake.run()
├── pancake.xml          # 插件和配置管理
├── pyproject.toml       # 依赖配置
└── src/
    ├── resource/
    │   ├── yaml/        # YAML 配置文件
    │   └── db/          # SQLite 数据库
    ├── mapper/          # 数据访问层
    └── controller/      # Web 控制器
```

## 使用方法

### Web 控制器

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

内置 CRUD：`select_by_id`、`select_list`、`select_one`、`select_count`、`insert`、`insert_batch`、`update_by_id`、`delete_by_id`。

链式查询：

```python
from pancake.ovenware.mybatis.wrapper import qw, uw

users = await mapper.select(qw().ge("age", 18).like("name", "%Ali%").orderByDesc("age").limit(50))
await mapper.update(uw().set("name", "Bob").eq("id", 1))
await mapper.delete(qw().lt("age", 18))
```

### 自动依赖注入

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

get_config()  # {"title": "我的应用", "port": 8080}
```

### IoC 容器

```python
container.register(UserService, UserService, Scope.SINGLETON)
service = container.resolve(UserService)
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

## 配置

### XML 启动配置 (`pancake.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
  <global>
    <service.title>我的应用</service.title>
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

- **`<global>`**：配置值合并到 YAML（XML 优先级高于 YAML）
- **`<plugin name="...">`**：省略 `source` 时自动推导为 `ovenware.<name>`
- **`init-order`**：加载顺序，数值越小越先加载（默认 0）
- **`enabled="false"`**：跳过插件初始化，但装饰器仍然加载
- **`${env:VAR_NAME}`**：引用环境变量

### 路径配置

所有路径可通过 `pancake.xml` 或 YAML 自定义：

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `paths.src_dir` | `src` | 用户代码根目录 |
| `paths.yaml_dir` | `src/resource/yaml` | YAML 配置目录 |
| `paths.json_dir` | `src/resource/json` | JSON 配置目录 |
| `paths.mapper_dir` | `src/mapper` | Mapper 目录 |
| `paths.controller_dir` | `src/controller` | 控制器目录 |
| `paths.db_dir` | `src/resource/db` | 数据库目录 |

### 服务和数据库配置

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `service.title` | `Pancake App` | 应用名称 |
| `service.version` | `1.0.0` | 应用版本 |
| `service.host` | `127.0.0.1` | 绑定地址 |
| `service.port` | `8080` | 绑定端口 |
| `mybatis.database.url` | `sqlite:///...` | 数据库连接 URL |
| `mybatis.database.min_size` | `1` | 连接池最小值 |
| `mybatis.database.max_size` | `5` | 连接池最大值 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `LOG_FILE` | 日志文件路径 |
| `EXTERNAL_PLUGIN_DIRS` | 外部插件路径（`;` 或 `:` 分隔） |
| `PANCAKE_AUTO_INSTALL` | 自动安装缺失依赖 |

## 可选依赖

```bash
pip install pancake[langgraph]   # LangGraph AI 工作流
pip install pancake[grpc]        # gRPC 远程调用
pip install pancake[redis]       # Redis 消息队列
pip install pancake[all]         # 全部可选依赖
```

## 运行测试

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 开源协议

MIT
