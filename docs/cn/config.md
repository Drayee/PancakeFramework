# 配置管理

Pancake 使用分层配置系统：XML > YAML > 默认值。

## YAML 配置

将 YAML 文件放在 `src/resource/yaml/`，所有文件自动加载合并。

### 服务配置

```yaml
# src/resource/yaml/service.yaml
service:
  title: 我的应用
  version: 1.0.0
  host: 127.0.0.1
  port: 8080
```

### 数据库配置

```yaml
# src/resource/yaml/mybatis.yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db
    min_size: 1
    max_size: 5
```

### 环境变量引用

使用 `${ENV_VAR}` 语法引用环境变量：

```yaml
mybatis:
  database:
    url: ${DATABASE_URL}

redis:
  password: ${REDIS_PASSWORD}
```

## XML 配置

项目根目录的 `pancake.xml` 控制全局设置和插件。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <global>
        <service.title>我的应用</service.title>
        <service.version>1.0.0</service.version>
        <service.host>127.0.0.1</service.host>
        <service.port>8080</service.port>
    </global>
    <plugins>
        <plugin name="embed" init-order="0"/>
        <plugin name="mybatis" init-order="1"/>
        <plugin name="web" init-order="2"/>
    </plugins>
</pancake>
```

## 环境变量

项目根目录的 `.env` 文件通过 `python-dotenv` 自动加载。

```
DATABASE_URL=sqlite:///resource/db/app.db
SECRET_KEY=my-secret
```

## 配置优先级

```
XML 全局配置 > YAML 配置 > 默认值
```

## 扁平化键访问

嵌套 YAML 键使用点号扁平化：

```yaml
service:
  title: 我的应用
  port: 8080
```

访问方式：
- `service.title`
- `service.port`

## 编程访问

```python
from pancake import settings

# 获取配置值
title = settings.get("service.title", "默认标题")
port = settings.get("service.port", 8080)

# 获取路径配置（返回绝对路径）
yaml_dir = settings.get_path("yaml_dir")
mapper_dir = settings.get_path("mapper_dir")

# 按前缀获取所有配置
service_config = settings.get_all("service.")

# 手动设置配置
settings.set("custom.key", "value")
```

## 默认配置项

| 键 | 默认值 |
|----|--------|
| `paths.src_dir` | `src` |
| `paths.yaml_dir` | `src/resource/yaml` |
| `paths.json_dir` | `src/resource/json` |
| `paths.mapper_dir` | `src/mapper` |
| `paths.controller_dir` | `src/controller` |
| `paths.db_dir` | `src/resource/db` |
| `paths.template_dir` | `src/templates` |
| `paths.static_dir` | `src/static` |
| `service.title` | `Pancake App` |
| `service.version` | `1.0.0` |
| `service.host` | `127.0.0.1` |
| `service.port` | `8080` |

## 配置热重载

`config_watcher` 模块监听 YAML/JSON 文件变更并自动重载。通过服务配置启用。
