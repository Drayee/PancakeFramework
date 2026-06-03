# Configuration

Pancake uses a layered configuration system: XML > YAML > defaults.

## YAML Configuration

Place YAML files in `src/resource/yaml/`. All files are loaded and merged automatically.

### Service Config

```yaml
# src/resource/yaml/service.yaml
service:
  title: My App
  version: 1.0.0
  host: 127.0.0.1
  port: 8080
```

### Database Config

```yaml
# src/resource/yaml/mybatis.yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db
    min_size: 1
    max_size: 5
```

### Environment Variable References

Use `${ENV_VAR}` syntax to reference environment variables:

```yaml
mybatis:
  database:
    url: ${DATABASE_URL}

redis:
  password: ${REDIS_PASSWORD}
```

## XML Configuration

`pancake.xml` in the project root controls global settings and plugins.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <global>
        <service.title>My App</service.title>
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

## Environment Variables

`.env` file in the project root is loaded automatically via `python-dotenv`.

```
DATABASE_URL=sqlite:///resource/db/app.db
SECRET_KEY=my-secret
```

## Config Priority

```
XML global > YAML > Default values
```

## Flat Key Access

Nested YAML keys are flattened with dots:

```yaml
service:
  title: My App
  port: 8080
```

Accessed as:
- `service.title`
- `service.port`

## Programmatic Access

```python
from pancake import settings

# Get any config value
title = settings.get("service.title", "Default Title")
port = settings.get("service.port", 8080)

# Get path configs (returns absolute path)
yaml_dir = settings.get_path("yaml_dir")
mapper_dir = settings.get_path("mapper_dir")

# Get all config with prefix
service_config = settings.get_all("service.")

# Manually set config
settings.set("custom.key", "value")
```

## Settings Defaults

| Key | Default |
|-----|---------|
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

## Config Hot-Reload

The `config_watcher` module watches YAML/JSON files for changes and reloads automatically. Enable in service config.
