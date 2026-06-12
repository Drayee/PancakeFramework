# 8. Web 插件 — Web 服务器

[← 上一节](07-mybatis.md) | [下一节 →](09-web-template.md)

---

## 概述

`pancake-web` 提供 aiohttp 驱动的 Spring MVC 风格 Web 服务器，支持控制器、参数绑定、中间件、异常处理、CORS。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web</artifactId>
</dependency>
```

## 配置

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

## 控制器

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

## HTTP 方法装饰器

| 装饰器 | 用途 |
|--------|------|
| `@get(path)` | GET 请求 |
| `@post(path)` | POST 请求 |
| `@put(path)` | PUT 请求 |
| `@delete(path)` | DELETE 请求 |

## 参数绑定

### 路径变量

```python
@get("/users/{id}")
async def get_user(self, id: int = path_variable()):
    return {"id": id}
```

### 查询参数

```python
@get("/search")
async def search(self, keyword: str = request_param(), page: int = request_param(default=1)):
    return {"keyword": keyword, "page": page}
```

### 请求体

```python
@post("/users")
async def create_user(self, body: dict = request_body()):
    return body

# 自动解析为 Struct/dataclass
@post("/users")
async def create_user(self, body: UserForm = request_body()):
    return body
```

## 返回值自动转换

| 返回值类型 | 转换结果 |
|-----------|---------|
| `None` | 204 No Content |
| `web.Response` | 原样返回 |
| `(data, status)` | JsonResponse(data, status) |
| `dataclass/Struct` | JsonResponse(asdict(data)) |
| `dict/list` | JsonResponse |
| `str` | HtmlResponse |

## 中间件

```python
# 类形式
@middleware(order=0)
class LoggingMiddleware:
    async def process(self, request, handler):
        logger.info(f"{request.method} {request.path}")
        response = await handler(request)
        return response

# 函数形式
@middleware(order=1)
async def timing_middleware(request, handler):
    import time
    start = time.time()
    response = await handler(request)
    duration = time.time() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response
```

`order` 越小越先执行。

## 异常处理

```python
@exception_handler(ValueError)
async def handle_value_error(request, exc):
    return JsonResponse({"error": str(exc)}, status=400)

@exception_handler(PermissionError)
async def handle_permission_error(request, exc):
    return JsonResponse({"error": "Forbidden"}, status=403)
```

## Controller 依赖注入

Controller 由 IoC 容器管理，支持 `@inject`：

```python
@controller("/api/orders")
@inject
class OrderController:
    order_service: OrderService  # 自动注入

    @get("/")
    async def list_orders(self, request):
        return await self.order_service.find_all()
```

## 静态文件

配置 `pancake.web.static` 目录后，自动挂载到 `/static`：

```yaml
pancake:
  web:
    static: src/static
```

访问：`http://localhost:8080/static/css/style.css`

---

[← 上一节](07-mybatis.md) | [下一节 →](09-web-template.md)
