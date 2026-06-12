# 5. 插件系统

[← 上一节](04-config.md) | [下一节 →](06-embed.md)

---

## 插件架构

Pancake 采用插件化架构。所有扩展功能（ORM、Web、AI 等）都通过插件提供。

插件的加载顺序由 `init_order` 控制（值小先加载）：

| 插件 | init_order | 说明 |
|------|-----------|------|
| mybatis | 1 | 数据库 ORM |
| redis | 2 | Redis 缓存 |
| ai | 4 | AI 模型 |
| web | 50 | Web 服务器 |
| web-template | 51 | 模板渲染 |
| web-security | 52 | 安全模块 |
| cui | 50 | CLI 框架 |
| gui | 70 | GUI 框架 |
| remote | 80 | 远程调用 |
| langgraph | 90 | 工作流 |
| embed | 999 | 零 import（最后加载） |

## 声明插件

在 `pancake.xml` 的 `<dependencies>` 中声明：

```xml
<dependencies>
    <!-- 框架插件 -->
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

    <!-- 第三方包 -->
    <dependency>
        <groupId>pypi</groupId>
        <artifactId>requests</artifactId>
    </dependency>
</dependencies>
```

## 自动安装

插件未安装时，框架会自动 `pip install`：

```
io.pancake + mybatis  →  pip install pancake_mybatis
io.pancake + web      →  pip install pancake_web
pypi + requests       →  pip install requests
```

## 禁用插件

```xml
<config>
    <framework.disable_dlc>["mybatis", "redis"]</framework.disable_dlc>
</config>
```

## 启用/禁用单个插件

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>mybatis</artifactId>
    <enabled>false</enabled>
</dependency>
```

## CLI 管理

```bash
pancake plugin list              # 列出已配置的插件
pancake plugin add <name>        # 添加插件
pancake plugin remove <name>     # 移除插件
pancake plugin clear             # 清空所有插件
```

## 自定义插件

在 `pancake/ovenware/` 下创建 `.py` 文件，定义 `Main` 类：

```python
from pancake.ovenware import InitAction

class Main(InitAction):
    init_order = 100
    build_order = 0

    def check(self) -> bool:
        """环境检查"""
        return True

    def build(self):
        """构建阶段"""
        pass

    async def startup(self):
        """启动阶段"""
        pass

    async def shutdown(self):
        """关闭阶段"""
        pass

    async def loop_method(self):
        """循环方法（如 Web 服务器）"""
        pass
```

---

[← 上一节](04-config.md) | [下一节 →](06-embed.md)
