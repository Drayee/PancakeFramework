# 1. 快速开始

[← 目录](README.md) | [下一节 →](02-core-concepts.md)

---

## 安装

```bash
pip install pancake_framework
```

## 创建项目

```bash
pancake create myapp
cd myapp
```

生成的项目结构：

```
myapp/
├── main.py                  # 入口文件
├── pancake.xml              # 插件配置
├── pyproject.toml           # 项目元数据
└── src/
    ├── resource/
    │   ├── yaml/            # YAML 配置
    │   │   └── service.yaml
    │   └── json/            # JSON 配置
    ├── templates/           # HTML 模板
    └── mapper/              # Mapper 层
```

## 入口文件

```python
import pancake

if __name__ == "__main__":
    pancake.run()
```

## 运行

```bash
python main.py
```

## 启动流程

```
main.py → pancake.run()
  ├── init()                    # 环境检查、结构检查
  └── run()
      ├── load_xml()            # 加载 pancake.xml → 插件列表 + 全局配置
      ├── load_config()         # 加载 YAML/JSON → settings
      ├── load_ovenware()       # 加载插件 (按 init_order 排序)
      ├── load_dish()           # 加载用户代码 src/
      ├── build()               # 创建 Bean → 拓扑排序 → 生命周期
      └── run_loop_methods()    # 运行 loop_method (如 Web 服务器)
```

## 第一个应用

### 项目配置

`pancake.xml`：

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

### 用户代码

`src/app.py`：

```python
# 无需 import（embed 插件已注入 builtins）

@controller("/api")
class AppController:
    @get("/hello")
    async def hello(self, request):
        return {"message": "Hello, Pancake!"}

    @get("/hello/{name}")
    async def hello_name(self, name: str = path_variable()):
        return {"message": f"Hello, {name}!"}
```

### 运行

```bash
python main.py
# 访问 http://127.0.0.1:8080/api/hello
```

---

[← 目录](README.md) | [下一节 →](02-core-concepts.md)
