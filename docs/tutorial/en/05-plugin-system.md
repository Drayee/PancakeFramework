# 5. Plugin System

[← Previous](04-config.md) | [Next →](06-embed.md)

---

## Plugin Architecture

Pancake uses a plugin architecture. All extensions (ORM, Web, AI, etc.) are provided as plugins.

Plugin loading order is controlled by `init_order` (lower value loads first):

| Plugin | init_order | Description |
|--------|-----------|-------------|
| mybatis | 1 | Database ORM |
| redis | 2 | Redis cache |
| ai | 4 | AI models |
| web | 50 | Web server |
| web-template | 51 | Template rendering |
| web-security | 52 | Security |
| cui | 50 | CLI framework |
| gui | 70 | GUI framework |
| remote | 80 | Remote calls |
| langgraph | 90 | Workflow |
| embed | 999 | Zero import (loads last) |

## Declaring Plugins

Declare in `pancake.xml` `<dependencies>`:

```xml
<dependencies>
    <!-- Framework plugin -->
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

    <!-- Third-party package -->
    <dependency>
        <groupId>pypi</groupId>
        <artifactId>requests</artifactId>
    </dependency>
</dependencies>
```

## Auto Install

When a plugin is not installed, the framework auto-runs `pip install`:

```
io.pancake + mybatis  →  pip install pancake_mybatis
io.pancake + web      →  pip install pancake_web
pypi + requests       →  pip install requests
```

## Disabling Plugins

```xml
<config>
    <framework.disable_dlc>["mybatis", "redis"]</framework.disable_dlc>
</config>
```

## Enable/Disable Single Plugin

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>mybatis</artifactId>
    <enabled>false</enabled>
</dependency>
```

## CLI Management

```bash
pancake plugin list              # List configured plugins
pancake plugin add <name>        # Add plugin
pancake plugin remove <name>     # Remove plugin
pancake plugin clear             # Clear all plugins
```

## Custom Plugin

Create a `.py` file under `pancake/ovenware/`, define a `Main` class:

```python
from pancake.ovenware import InitAction

class Main(InitAction):
    init_order = 100
    build_order = 0

    def check(self) -> bool:
        """Environment check"""
        return True

    def build(self):
        """Build phase"""
        pass

    async def startup(self):
        """Startup phase"""
        pass

    async def shutdown(self):
        """Shutdown phase"""
        pass

    async def loop_method(self):
        """Loop method (e.g. Web server)"""
        pass
```

---

[← Previous](04-config.md) | [Next →](06-embed.md)
