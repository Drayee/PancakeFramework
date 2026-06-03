# Web 模块

Pancake 底层使用 FastAPI。所有装饰器自动注入 builtins，无需 import。

## 控制器

```python
@get_controller("/users")
async def list_users():
    return await UserMapper().select_list()

@post_controller("/users")
async def create_user(name: str, age: int):
    return {"id": await UserMapper().insert(name=name, age=age)}

@put_controller("/users/{user_id}")
async def update_user(user_id: int, name: str):
    await UserMapper().update_by_id(id=user_id, name=name)

@delete_controller("/users/{user_id}")
async def delete_user(user_id: int):
    await UserMapper().delete_by_id(user_id)
```

### 页面控制器（模板渲染）

```python
@page_controller("/home", template="home.html")
async def home():
    return {"title": "首页", "message": "你好"}
```

模板默认从 `src/templates/` 加载，可通过 `service.template_dir` 配置。

## 过滤器链

类似 Spring Security 的过滤器链。支持两种风格：

### 函数风格

```python
@filter(order=10)
async def auth_filter(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token and request.url.path.startswith("/api"):
        return JSONResponse(status_code=401, content={"detail": "未授权"})
    return await call_next(request)
```

### 类风格

```python
class AuthFilter(Filter):
    order = 10

    async def do_filter(self, request, call_next):
        if not request.headers.get("Authorization"):
            return JSONResponse(status_code=401)
        return await call_next(request)
```

### 内置过滤器

- **MetricsFilter** (order=900) — 收集请求指标。通过 `service.metrics_enabled: false` 禁用。

## 认证与授权

```python
@set_auth_handler
async def authenticate(request, token):
    user = await verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

@get_controller("/profile")
@auth_required
async def get_profile(current_user):
    return {"user": current_user}

@delete_controller("/admin/users/{user_id}")
@role_required("admin")
async def delete_user(user_id: int):
    await UserMapper().delete_by_id(user_id)
```

## 中间件

```python
@middleware(order=1)
async def log_request(request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} {time.time()-start:.3f}s")
    return response
```

## 限流

```python
@get_controller("/api/data")
@rate_limit(times=100, seconds=60)
async def get_data():
    return {"data": "..."}
```

## 事务

```python
@post_controller("/transfer")
@transaction
async def transfer(from_id: int, to_id: int, amount: float):
    # 该函数内的所有数据库操作在同一事务中执行
    ...
```

## 参数校验

```python
@post_controller("/users")
@validate(age=lambda v: 0 < v < 200, name=lambda v: len(v) > 0)
async def create_user(name: str, age: int):
    ...
```

## WebSocket

```python
@websocket_controller("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## 静态文件

将静态文件放在 `src/static/`，自动通过 `/static` 路径提供服务。配置：

```yaml
service:
  static_dir: src/static
  static_url: /static
```

## 指标

当 `service.metrics_enabled` 为 true（默认）时，MetricsFilter 收集请求数据。

- `GET /health` — 健康检查
- `GET /metrics` — 请求指标（计数、错误率、延迟）
