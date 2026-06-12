# 9. Web Template Plugin — Template Rendering

[← Previous](08-web.md) | [Next →](10-web-security.md)

---

## Overview

`pancake-web-template` provides Jinja2 template engine integration for `pancake-web`, enabling HTML page rendering.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-template</artifactId>
</dependency>
```

## Using @template Decorator

```python
@controller("/")
class HomeController:
    @get("/")
    @template("home.html")
    async def home(self, request):
        return {"title": "Home", "items": ["Python", "Pancake", "IoC"]}
```

Template file `src/templates/home.html`:

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

When a handler returns a `dict`, it's auto-rendered as an HTML page. The `request` object is auto-injected into the template context.

## Manual Rendering

```python
@controller("/pages")
class PageController:
    @get("/about")
    async def about(self, request):
        return render("about.html", title="About Us")
```

## Custom Filters

```python
register_filter("reverse", lambda s: s[::-1])
register_filter("upper", lambda s: s.upper())
```

Usage in templates:

```html
{{ name | reverse }}
{{ name | upper }}
```

---

[← Previous](08-web.md) | [Next →](10-web-security.md)
