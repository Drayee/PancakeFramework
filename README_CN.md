# Pancake Framework

> 装饰器驱动的 Python 全栈框架，集成 Spring 风格 IoC、MyBatis Plus ORM、AI 工作流和插件系统。

[English](./README.md) | [中文文档](./README_CN.md)

## 特性

- **Dough IoC 容器** — Spring 风格 Bean 管理，完整生命周期：`on_init` → `on_start` → `on_stop` → `on_destroy`
- **装饰器驱动** — `@singleton`、`@prototype`、`@lazy`、`@inject`、`@config`、`@depends_on`
- **异步优先** — 所有生命周期方法支持 `async def`，DoughFactory 自动处理 sync/async
- **零 import** — `pancake-embed` 插件将所有装饰器和类注入 `builtins`，无需显式 import
- **基类体系** — `Configuration`（Bean 工厂）、`Service`（服务）、`Struct`（数据结构）、`Function`（函数包装）
- **MyBatis Plus ORM** — `@Mapper`、`@Select`/`@Insert`/`@Update`/`@Delete`、链式查询 `qw()`、动态 SQL、分页
- **aiohttp Web 服务器** — `@controller`、`@get`/`@post`、参数绑定、中间件、异常处理、CORS
- **Jinja2 模板** — `@template` 装饰器自动渲染 HTML 页面
- **Spring Security 风格安全** — 认证/授权、JWT、CSRF 防护、限流、安全响应头
- **AI 模块** — 统一 LLM 客户端（OpenAI/DeepSeek/Gemini/Ollama）、短期/长期记忆、RAG
- **Redis 缓存** — `@cached` 装饰器、CacheGuard（防穿透/雪崩/击穿）
- **消息队列** — `@event_node`/`@on_event` 事件驱动，SimpleBroker/RedisBroker
- **远程调用** — `HttpRemote`/`GrpcRemote` HTTP 和 gRPC 客户端
- **LangGraph 工作流** — `@langgraph_node`/`@langgraph_edge` 状态图编排
- **GUI/CUI** — Flet 桌面 GUI 和 Click CLI 框架集成
- **插件系统** — XML 声明式管理，自动 pip 安装，`pancake plugin` CLI

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
python main.py
# 或
pancake run
```

### 项目结构

```
myapp/
├── main.py                  # 入口文件
├── pancake.xml              # 插件和全局配置
├── pyproject.toml           # 项目元数据
└── src/
    ├── resource/
    │   ├── yaml/            # YAML 配置
    │   │   └── service.yaml
    │   └── json/            # JSON 配置
    └── templates/           # HTML 模板
```

## 核心概念

### Dough IoC 系统

Pancake 的核心是 **Dough** 系统 — Spring 风格的 IoC 容器。所有 Bean 继承自 `Dough` 基类，由 `DoughFactory` 统一管理生命周期。

#### Bean 生命周期

```
__init__()  →  on_init()  →  on_start()  →  [运行中]  →  on_stop()  →  on_destroy()
   构造        @PostConstruct    就绪                        停止         @PreDestroy
```

#### 作用域

| 作用域 | 装饰器 | 说明 |
|--------|--------|------|
| 单例 | `@singleton` | 每个工厂一个实例（默认） |
| 多例 | `@prototype` | 每次获取创建新实例 |
| 懒加载 | `@lazy` | 首次访问时创建 |

#### 基类

| 基类 | 用途 |
|------|------|
| `Service` | 服务类，方法集合 |
| `Configuration` | 配置类，非私有方法返回值自动注册为 Bean |
| `Struct` | 数据结构，继承 dataclass，适用于 DTO/表单 |
| `Function` | 函数包装，提供 `call()` 方法 |

### 零 import 机制

启用 `pancake-embed` 插件后，所有框架装饰器、基类和服务自动注入 `builtins`：

```python
# 无需任何 import，直接使用
@singleton
@depends_on("DatabaseService")
class UserService(Service):
    async def on_init(self):
        self.db = DoughFactory.get().resolve("DatabaseService")

    async def find_user(self, user_id: int):
        return await self.db.query(user_id)
```

### 装饰器一览

| 装饰器 | 目标 | 说明 |
|--------|------|------|
| `@dough` | 类 | 标记类为 Bean |
| `@singleton` | 类 | 单例作用域 |
| `@prototype` | 类 | 多例作用域 |
| `@lazy` | 类 | 懒加载 |
| `@service` | 类 | 转换为 Service 子类 |
| `@configuration` | 类 | 转换为 Configuration 子类 |
| `@struct` | 类 | 标记为数据结构（dataclass） |
| `@function` | 函数 | 转换为 Function 子类 |
| `@inject` | 类/函数 | 自动按类型注入依赖 |
| `@inject_name` | 类/函数 | 自动按名称注入依赖 |
| `@config` | 类 | 从配置注入 Struct 字段 |
| `@depends_on("A", "B")` | 类 | 声明 Bean 依赖 |
| `@import_class(Cls)` | 类 | 自动注册外部类到工厂 |
| `@maker` | 方法 | 标记方法返回值为 Bean |
| `@no_maker` | 方法 | 排除方法，不自动注册 |

## 插件系统

Pancake 采用插件化架构，所有扩展功能通过插件提供。插件通过 `pancake.xml` 的 `<dependencies>` 声明。

### 插件列表

| 插件 | 包名 | 说明 |
|------|------|------|
| **embed** | `pancake-embed` | 零 import 机制，注入 builtins |
| **mybatis** | `pancake-mybatis` | MyBatis Plus ORM |
| **web** | `pancake-web` | aiohttp Web 服务器 |
| **web-template** | `pancake-web-template` | Jinja2 模板渲染 |
| **web-security** | `pancake-web-security` | Spring Security 风格安全 |
| **ai** | `pancake-ai` | AI 模型集成 |
| **redis** | `pancake-redis` | Redis 缓存 |
| **langgraph** | `pancake-langgraph` | LangGraph 工作流 |
| **remote** | `pancake-remote` | HTTP/gRPC 远程调用 |
| **cui** | `pancake-cui` | Click CLI 框架 |
| **gui** | `pancake-gui` | Flet 桌面 GUI |

### 插件管理

```bash
pancake plugin list              # 列出已配置的插件
pancake plugin add <name>        # 添加插件到 pancake.xml
pancake plugin remove <name>     # 移除插件
pancake plugin clear             # 清空所有插件
```

### pancake.xml 配置

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

## 文档

| 模块                                                         | 说明                                                       |
|------------------------------------------------------------|----------------------------------------------------------|
| [框架教程 (中文)](docs/tutorial/zh/README.md)                    | 完整教程，涵盖核心概念和所有插件                                         |
| [Framework Tutorial (English)](docs/tutorial/en/README.md) | Complete tutorial covering core concepts and all plugins |

## 可选依赖

```bash
pip install pancake_framework[ai]          # AI 模块 (openai)
pip install pancake_framework[redis]       # Redis 缓存
pip install pancake_framework[sqlite]      # SQLite 数据库
pip install pancake_framework[postgres]    # PostgreSQL 数据库
pip install pancake_framework[mysql]       # MySQL 数据库
pip install pancake_framework[langgraph]   # LangGraph 工作流
pip install pancake_framework[grpc]        # gRPC 远程调用
pip install pancake_framework[gui]         # Flet GUI
pip install pancake_framework[all]         # 全部可选依赖
```

## 项目结构

```
pancake/                    # 框架核心
├── __init__.py             # 入口: init() → run()
├── run.py                  # 启动流水线: load_xml → load_config → load_ovenware → load_dish → build
├── dough.py                # Dough 基类、Scope 枚举、DoughMeta 元类
├── registry.py             # 全局注册表: flour/water/egg/sugar
├── decorators/             # 装饰器: scope/bean/inject/config/convert
├── settings.py             # 集中配置管理
├── base/                   # 基类: Configuration、Service、Struct、Function
├── factory/                # DoughFactory Bean 工厂 + PackageManager
├── builder/                # 构建流水线: load_dlc(插件) + load_src(用户代码) + build
├── cli/                    # CLI: init/create/run/check/build/plugin/config/audit
├── ovenware/               # 插件基类 InitAction + Broker 消息队列
├── resource/               # 配置加载: YAML/JSON/XML + 日志 + 热重载
└── tool/                   # 工具: ProgressBar
```

## CLI 命令

```bash
pancake version              # 显示版本
pancake init                 # 在当前目录初始化项目
pancake create <name>        # 创建新项目
pancake run                  # 运行项目
pancake check                # 检查项目结构和环境
pancake build                # 打包项目为 wheel
pancake config show          # 显示当前配置
pancake audit                # 审核代码质量
pancake update               # 更新框架
pancake install              # 安装缺失依赖
```

## 启动流程

```
main.py → pancake.run()
  ├── init()                    # 环境检查、结构检查、加载 dotenv/logging
  └── run.py → run()
      ├── load_xml()            # 加载 pancake.xml → 插件列表 + 全局配置
      ├── load_config()         # 加载 YAML/JSON → settings
      ├── load_ovenware()       # 加载插件 (按 init_order 排序)
      ├── load_dish()           # 加载用户代码 src/
      ├── build()               # 创建 Bean → 拓扑排序 → on_init → on_start
      └── run_loop_methods()    # 运行 loop_method (如 Web 服务器)
```

## 测试

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 开源协议

MIT
