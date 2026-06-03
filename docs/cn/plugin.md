# 插件系统

Pancake 自动发现并加载 `ovenware/` 目录下的插件。每个插件是包含 `Main` 类的 `.py` 文件或包。

## 插件结构

```python
# pancake/ovenware/my_plugin.py
from pancake.ovenware import InitAction

class Main(InitAction):
    init_order = 10       # 加载顺序（值小先加载）
    _dependencies = []    # 所需 pip 包
    _extras = "my_extra"  # extras_require 组

    def __init__(self):
        # 初始化逻辑
        pass

    @staticmethod
    def check():
        # 检查依赖
        check_dependencies(Main._dependencies, Main._extras)

    def build(self):
        # 初始化后的构建步骤
        pass

    def loop_method(self):
        # 服务启动后执行
        pass
```

## 加载顺序

控制插件加载顺序，值小先加载。

| 插件 | init_order |
|------|------------|
| `embed` | -10（最后加载，注入 builtins） |
| `mybatis` | 1 |
| `redis_cache` | 2 |
| `ai_model` | 4 |
| `web` | 50 |

## 外部插件

设置 `EXTERNAL_PLUGIN_DIRS` 环境变量从自定义目录加载插件：

```bash
export EXTERNAL_PLUGIN_DIRS="/path/to/plugins"
```

## 禁用插件

通过 YAML 禁用内置插件：

```yaml
framework:
  disable_dlc:
    - langgraph
    - external_plugin
```

或通过 `pancake.xml`：

```xml
<plugins>
    <plugin name="langgraph" enabled="false"/>
</plugins>
```

## CLI 插件管理

```bash
# 列出所有插件及状态
pancake plugin list

# 添加插件到 pancake.xml
pancake plugin add my_plugin
```

## 注册

插件向 `oven` 注册表注册装饰器、类和实例：

```python
from pancake import oven

# 装饰器（自动注入 builtins）
oven.muffin_flour["my_decorator"] = my_decorator

# 类
oven.muffin_water["MyClass"] = MyClass

# 实例 / 工厂
oven.muffin_sugar["my_service"] = get_my_service

# 配置值
oven.pancake_yaml["custom.key"] = "value"
```

## 内置插件

| 插件 | 说明 |
|------|------|
| `embed` | 将所有注册项注入 builtins |
| `mybatis` | ORM：Mapper、SQL 解析、连接管理 |
| `web` | FastAPI Web 服务、控制器、过滤器、认证 |
| `redis_cache` | Redis 客户端、缓存防护、`@cached` |
| `ai_model` | LLM 客户端、记忆、RAG |
| `broker` | 消息队列 (SimpleBroker / RedisBroker) |
| `lifecycle` | 生命周期钩子 (init/start/stop/error) |
| `remote` | HTTP 和 gRPC 远程调用 |
| `langgraph` | AI 工作流节点和边 |
| `external_plugin` | 外部插件加载器 |
