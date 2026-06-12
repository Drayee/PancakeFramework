# 8. Web Plugin — Web Server

[← Previous](07-mybatis.md) | [Next →](09-web-template.md)

---

## Overview

`pancake-web` provides an aiohttp-powered Spring MVC-style web server with controllers, parameter binding, middleware, exception handling, and CORS.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web</artifactId>
</dependency>
```

## Configuration

```yaml
# src/resource/yaml/service.yaml
pancake:
  web:
    host: 127.0.0.1
    port: 8080
    debug: false
    static: src/static
    templates: src/templates
    cors:
      allow_origins: "*"
      allow_methods: "GET,POST,PUT,DELETE,OPTIONS"
    session:
      secret_key: your-secret-key
    request:
      timeout: 30
      max_body_size: 1048576
```

## Controllers

```python
@controller("/api/users")
class UserController:
    @get("/")
    async def list_users(self, request):
        return [{"id": 1, "name": "Alice"}]

    @get("/{id}")
    async def get_user(self, id: int = path_variable()):
        return {"id": id, "name": "Alice"}

    @post("/")
    async def create_user(self, body: dict = request_body()):
        return {"id": 3, **body}, 201

    @put("/{id}")
    async def update_user(self, id: int = path_variable(), body: dict = request_body()):
        return {"id": id, **body}

    @delete("/{id}")
    async def delete_user(self, id: int = path_variable()):
        return None  # 204 No Content
```

## HTTP Method Decorators

| Decorator | Purpose |
|-----------|---------|
| `@get(path)` | GET request |
| `@post(path)` | POST request |
| `@put(path)` | PUT request |
| `@delete(path)` | DELETE request |

## Parameter Binding

### Path Variables

```python
@get("/users/{id}")
async def get_user(self, id: int = path_variable()):
    return {"id": id}
```

### Query Parameters

```python
@get("/search")
async def search(self, keyword: str = request_param(), page: int = request_param(default=1)):
    return {"keyword": keyword, "page": page}
```

### Request Body

```python
@post("/users")
async def create_user(self, body: dict = request_body()):
    return body

# Auto-parse to Struct/dataclass
@post("/users")
async def create_user(self, body: UserForm = request_body()):
    return body
```

## Auto Response Conversion

| Return Type | Result |
|-------------|--------|
| `None` | 204 No Content |
| `web.Response` | As-is |
| `(data, status)` | JsonResponse(data, status) |
| `dataclass/Struct` | JsonResponse(asdict(data)) |
| `dict/list` | JsonResponse |
| `str` | HtmlResponse |

## Middleware

```python
# Class form
@middleware(order=0)
class LoggingMiddleware:
    async def process(self, request, handler):
        logger.info(f"{request.method} {request.path}")
        response = await handler(request)
        return response

# Function form
@middleware(order=1)
async def timing_middleware(request, handler):
    import time
    start = time.time()
    response = await handler(request)
    duration = time.time() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response
```

Smaller `order` = executes first.

## Exception Handling

```python
@exception_handler(ValueError)
async def handle_value_error(request, exc):
    return JsonResponse({"error": str(exc)}, status=400)

@exception_handler(PermissionError)
async def handle_permission_error(request, exc):
    return JsonResponse({"error": "Forbidden"}, status=403)
```

## Controller DI

Controllers are managed by IoC container, supporting `@inject`:

```python
@controller("/api/orders")
@inject
class OrderController:
    order_service: OrderService  # Auto-injected

    @get("/")
    async def list_orders(self, request):
        return await self.order_service.find_all()
```

## Static Files

After configuring `pancake.web.static`, auto-mounted at `/static`:

```yaml
pancake:
  web:
    static: src/static
```

Access: `http://localhost:8080/static/css/style.css`

---

[← Previous](07-mybatis.md) | [Next →](09-web-template.md)
