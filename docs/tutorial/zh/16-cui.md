# 16. CUI 插件 — 命令行界面

[← 上一节](15-remote.md) | [下一节 →](17-gui.md)

---

## 概述

`pancake-cui` 提供 Click 驱动的 CLI 框架，支持命令分组、彩色输出、进度条、交互式输入。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>cui</artifactId>
</dependency>
```

## 配置

```yaml
client:
  type: cui
  cui:
    app_name: mycli
    version: 1.0.0
```

## 定义命令

```python
@cui_command()
@cui_option("--name", prompt="Your name", help="Your name")
def greet(name: str):
    """打招呼"""
    cui_success(f"Hello, {name}!")

@cui_group()
class DatabaseCommands:
    """数据库管理命令"""

@cui_command(group="database")
@cui_option("--force", is_flag=True, help="Force reset")
def migrate(force: bool):
    """运行数据库迁移"""
    if force:
        cui_warning("Force reset!")
    cui_info("Migration complete")
```

## 输出工具

```python
cui_info("处理中...")        # 蓝色 [INFO]
cui_success("完成!")         # 绿色 [OK]
cui_warning("注意!")         # 黄色 [WARN]
cui_error("失败!")           # 红色 [ERROR]
cui_print("自定义", fg="cyan")  # 自定义颜色

name = cui_prompt("请输入名称")          # 交互输入
confirm = cui_prompt("确定吗?", type=bool)  # 确认输入

with cui_progress(100, "下载中") as p:
    for i in range(100):
        p.update(1)
```

---

[← 上一节](15-remote.md) | [下一节 →](17-gui.md)
