# Web Module

Pancake uses FastAPI under the hood. All decorators are auto-injected into builtins — no import needed.

## Controllers

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

### Page Controllers (Template Rendering)

```python
@page_controller("/home", template="home.html")
async def home():
    return {"title": "Home", "message": "Hello"}
```

Templates are loaded from `src/templates/` by default. Configure via `service.template_dir` in YAML.

## Filter Chain

Similar to Spring Security's filter chain. Two styles supported:

### Function Style

```python
@filter(order=10)
async def auth_filter(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token and request.url.path.startswith("/api"):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)
```

### Class Style

```python
class AuthFilter(Filter):
    order = 10

    async def do_filter(self, request, call_next):
        if not request.headers.get("Authorization"):
            return JSONResponse(status_code=401)
        return await call_next(request)
```

### Built-in Filters

- **MetricsFilter** (order=900) — Collects request metrics. Disable via `service.metrics_enabled: false` in YAML.

## Auth & Authorization

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

## Middleware

```python
@middleware(order=1)
async def log_request(request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} {time.time()-start:.3f}s")
    return response
```

## Rate Limiting

```python
@get_controller("/api/data")
@rate_limit(times=100, seconds=60)
async def get_data():
    return {"data": "..."}
```

## Transaction

```python
@post_controller("/transfer")
@transaction
async def transfer(from_id: int, to_id: int, amount: float):
    # All DB operations in this function run in a single transaction
    ...
```

## Validation

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

## Static Files

Place static files in `src/static/`. They are automatically served at `/static`. Configure via:

```yaml
service:
  static_dir: src/static
  static_url: /static
```

## Metrics

When `service.metrics_enabled` is true (default), a `MetricsFilter` collects request data.

- `GET /health` — Health check
- `GET /metrics` — Request metrics (count, errors, latency per path)
