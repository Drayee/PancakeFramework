# 1. Quick Start

[← Index](README.md) | [Next →](02-core-concepts.md)

---

## Install

```bash
pip install pancake_framework
```

## Create Project

```bash
pancake create myapp
cd myapp
```

Generated project structure:

```
myapp/
├── main.py                  # Entry point
├── pancake.xml              # Plugin config
├── pyproject.toml           # Project metadata
└── src/
    ├── resource/
    │   ├── yaml/            # YAML config
    │   │   └── service.yaml
    │   └── json/            # JSON config
    ├── templates/           # HTML templates
    └── mapper/              # Mapper layer
```

## Entry Point

```python
import pancake

if __name__ == "__main__":
    pancake.run()
```

## Run

```bash
python main.py
```

## Startup Flow

```
main.py → pancake.run()
  ├── init()                    # Environment check, structure check
  └── run()
      ├── load_xml()            # Load pancake.xml → plugins + config
      ├── load_config()         # Load YAML/JSON → settings
      ├── load_ovenware()       # Load plugins (sorted by init_order)
      ├── load_dish()           # Load user code from src/
      ├── build()               # Create Beans → topological sort → lifecycle
      └── run_loop_methods()    # Run loop_method (e.g. Web server)
```

## First Application

### Project Config

`pancake.xml`:

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
            <artifactId>web</artifactId>
        </dependency>
    </dependencies>
</pancake>
```

### User Code

`src/app.py`:

```python
# No import needed (embed plugin injects into builtins)

@controller("/api")
class AppController:
    @get("/hello")
    async def hello(self, request):
        return {"message": "Hello, Pancake!"}

    @get("/hello/{name}")
    async def hello_name(self, name: str = path_variable()):
        return {"message": f"Hello, {name}!"}
```

### Run

```bash
python main.py
# Visit http://127.0.0.1:8080/api/hello
```

---

[← Index](README.md) | [Next →](02-core-concepts.md)
