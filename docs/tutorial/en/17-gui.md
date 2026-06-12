# 17. GUI Plugin — Desktop UI

[← Previous](16-cui.md) | [Next →](18-cli.md)

---

## Overview

`pancake-gui` provides a Flet-powered desktop GUI framework.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>gui</artifactId>
</dependency>
```

## Defining Pages

```python
import flet as ft

@gui_page("/")
def home_page(page):
    """Home page"""
    page.add(
        ft.Text("Welcome to Pancake GUI!", size=30),
        ft.ElevatedButton("Click Me", on_click=lambda _: gui_action("greet")),
    )

@gui_action
def greet():
    print("Hello from Pancake!")
```

---

[← Previous](16-cui.md) | [Next →](18-cli.md)
