# 9. Web Template 插件 — 模板渲染

[← 上一节](08-web.md) | [下一节 →](10-web-security.md)

---

## 概述

`pancake-web-template` 提供 Jinja2 模板引擎集成，为 `pancake-web` 提供 HTML 页面渲染。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-template</artifactId>
</dependency>
```

## 使用 @template 装饰器

```python
@controller("/")
class HomeController:
    @get("/")
    @template("home.html")
    async def home(self, request):
        return {"title": "首页", "items": ["Python", "Pancake", "IoC"]}
```

模板文件 `src/templates/home.html`：

```html
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</body>
</html>
```

handler 返回 `dict` 时，自动渲染为 HTML 页面。`request` 对象会自动注入到模板上下文中。

## 手动渲染

```python
@controller("/pages")
class PageController:
    @get("/about")
    async def about(self, request):
        return render("about.html", title="关于我们")
```

## 自定义过滤器

```python
register_filter("reverse", lambda s: s[::-1])
register_filter("upper", lambda s: s.upper())
```

模板中使用：

```html
{{ name | reverse }}
{{ name | upper }}
```

---

[← 上一节](08-web.md) | [下一节 →](10-web-security.md)
