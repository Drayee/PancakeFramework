# 4. Configuration

[← Previous](03-ioc.md) | [Next →](05-plugin-system.md)

---

## Sources and Priority

```
pancake.xml <config>  →  YAML files  →  JSON files  →  defaults
         highest                                           lowest
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

Supports `${env:VAR_NAME}` to reference environment variables.

## YAML Config

Create `.yaml` files under `src/resource/yaml/`:

```yaml
# src/resource/yaml/service.yaml
service:
  title: myapp
  port: 8080

mybatis:
  database:
    url: sqlite:///resource/db/app.db
```

YAML supports `${key.path}` placeholders to reference other config values:

```yaml
app:
  name: myapp
  full_title: "${app.name} - Powered by Pancake"
# full_title = "myapp - Powered by Pancake"
```

## JSON Config

Create `.json` files under `src/resource/json/`, same structure as YAML.

## Reading Config

```python
from pancake import settings

# Get config
title = settings.get("service.title")
port = settings.get("service.port", 8080)  # with default

# Get all config
all_config = settings.get_all()
service_config = settings.get_all("service.")  # filter by prefix

# Manual set
settings.set("custom.key", "value")
```

## @config — Inject Struct Fields from Config

```python
@config
@struct
class DatabaseConfig:
    url: str = None
    min_size: int = None
    max_size: int = None
# Auto-reads databaseconfig.url, databaseconfig.min_size, etc. from settings
```

## Common Config Keys

| Key | Description | Default |
|-----|-------------|---------|
| `service.title` | App name | — |
| `service.version` | App version | — |
| `service.host` | Bind address | `127.0.0.1` |
| `service.port` | Bind port | `8080` |
| `mybatis.database.url` | Database URL | `sqlite:///resource/db/app.db` |
| `framework.disable_dlc` | Disabled plugins | `[]` |
| `framework.main_loop` | Main thread loop_method | — |

---

[← Previous](03-ioc.md) | [Next →](05-plugin-system.md)
