# 4. 配置系统

[← 上一节](03-ioc.md) | [下一节 →](05-plugin-system.md)

---

## 配置来源和优先级

```
pancake.xml <config>  →  YAML 文件  →  JSON 文件  →  默认值
         高优先级                                          低优先级
```

## pancake.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <config>
        <service.title>myapp</service.title>
        <service.port>8080</service.port>
        <mybatis.database.url>sqlite:///resource/db/app.db</mybatis.database.url>
    </config>
    <dependencies>
        <dependency>
            <groupId>io.pancake</groupId>
            <artifactId>embed</artifactId>
        </dependency>
    </dependencies>
</pancake>
```

支持 `${env:VAR_NAME}` 引用环境变量。

## YAML 配置

在 `src/resource/yaml/` 下创建 `.yaml` 文件：

```yaml
# src/resource/yaml/service.yaml
service:
  title: myapp
  port: 8080

mybatis:
  database:
    url: sqlite:///resource/db/app.db
```

YAML 支持 `${key.path}` 占位符引用其他配置值：

```yaml
app:
  name: myapp
  full_title: "${app.name} - Powered by Pancake"
# full_title = "myapp - Powered by Pancake"
```

## JSON 配置

在 `src/resource/json/` 下创建 `.json` 文件，格式与 YAML 相同。

## 读取配置

```python
from pancake import settings

# 获取配置
title = settings.get("service.title")
port = settings.get("service.port", 8080)  # 带默认值

# 获取所有配置
all_config = settings.get_all()
service_config = settings.get_all("service.")  # 按前缀过滤

# 手动设置
settings.set("custom.key", "value")
```

## @config — 从配置注入 Struct 字段

```python
@config
@struct
class DatabaseConfig:
    url: str = None
    min_size: int = None
    max_size: int = None
# 自动从 settings 读取 databaseconfig.url、databaseconfig.min_size 等
```

## 常用配置项

| 键 | 说明 | 默认值 |
|----|------|--------|
| `service.title` | 应用名称 | — |
| `service.version` | 应用版本 | — |
| `service.host` | 绑定地址 | `127.0.0.1` |
| `service.port` | 绑定端口 | `8080` |
| `mybatis.database.url` | 数据库 URL | `sqlite:///resource/db/app.db` |
| `framework.disable_dlc` | 禁用插件列表 | `[]` |
| `framework.main_loop` | 主线程 loop_method | — |

---

[← 上一节](03-ioc.md) | [下一节 →](05-plugin-system.md)
