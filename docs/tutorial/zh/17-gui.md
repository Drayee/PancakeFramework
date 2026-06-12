# 17. GUI 插件 — 桌面界面

[← 上一节](16-cui.md) | [下一节 →](18-cli.md)

---

## 概述

`pancake-gui` 提供 Flet 驱动的桌面 GUI 框架。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>gui</artifactId>
</dependency>
```

## 定义页面

```python
import flet as ft

@gui_page("/")
def home_page(page):
    """首页"""
    page.add(
        ft.Text("Welcome to Pancake GUI!", size=30),
        ft.ElevatedButton("Click Me", on_click=lambda _: gui_action("greet")),
    )

@gui_action
def greet():
    print("Hello from Pancake!")
```

---

[← 上一节](16-cui.md) | [下一节 →](18-cli.md)
