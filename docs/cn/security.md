# 安全模块

内置安全功能：密码哈希、API Key 认证、CSRF 防护、安全响应头、IP 过滤、会话管理、OAuth2 服务器。

## 密码哈希

自动检测最佳库：bcrypt > argon2 > hashlib（回退）。

```python
# 哈希密码
hashed = hash_password("my-secret")

# 验证密码
is_valid = verify_password("my-secret", hashed)
```

验证时自动检测哈希格式：`$2b$...` (bcrypt)、`$argon2$...`、`$sha256$salt$hash`。

## API Key 认证

```python
@get_controller("/api/data")
@api_key_required(keys=["secret-key-123"])
async def get_data():
    return {"data": "..."}
```

### 自定义验证器

```python
async def validate_api_key(key: str) -> bool:
    return await db.exists("api_keys", key=key)

@get_controller("/api/data")
@api_key_required(validator=validate_api_key)
async def get_data():
    ...
```

### 自定义 Header

```python
@api_key_required(header="Authorization", keys=["Bearer my-key"])
async def get_data():
    ...
```

## 安全响应头

启用后（默认开启）自动为所有响应添加安全头。

| Header | 值 |
|--------|-----|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Strict-Transport-Security | （可选，见配置） |
| Content-Security-Policy | （可选，见配置） |

### 配置

```yaml
service:
  security_headers:
    enabled: true
    hsts: true
    csp: "default-src 'self'"
```

## IP 过滤

支持 CIDR 格式的 IP 黑白名单。

```yaml
service:
  # 白名单模式：只有这些 IP 可以访问
  ip_whitelist:
    - "127.0.0.1"
    - "10.0.0.0/8"

  # 黑名单模式：这些 IP 被封禁
  ip_blacklist:
    - "192.168.1.100"
    - "10.0.0.0/24"
```

同时配置白名单和黑名单时，白名单优先。

## CSRF 防护

保护 POST/PUT/DELETE/PATCH 请求。GET/HEAD/OPTIONS 自动豁免。

### 生成令牌

```python
token = generate_csrf_token()
```

### 提交令牌

通过表单字段：
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    ...
</form>
```

或通过 header：
```javascript
fetch("/api/data", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken }
});
```

### 配置

```yaml
service:
  csrf:
    enabled: true
    exempt_paths:
      - "/api/"       # API 端点豁免 CSRF
      - "/webhook/"
```

## 会话管理

基于 cookie 的服务端会话。支持 memory（默认）和 Redis 后端。

```python
# 获取会话数据
session = await get_session(request)

# 在路由中手动控制会话
@post_controller("/login")
async def login(request: Request, username: str, password: str):
    session_mgr = SessionManager()
    session = await session_mgr.get_session(request)
    session["user_id"] = user.id
    response = JSONResponse({"status": "ok"})
    await session_mgr.save_session(request, response, session)
    return response
```

### 配置

```yaml
service:
  session:
    backend: memory    # memory | redis
    ttl: 3600
    cookie_name: pancake_session
```

## OAuth2 服务器

完整的 OAuth2 授权服务器，基于 JWT 令牌。

### 注册客户端

```python
server = OAuth2Server()
server.register_client(
    client_id="myapp",
    client_secret="secret",
    redirect_uris=["http://localhost:8080/callback"],
    scopes=["read", "write"],
    grant_types=["authorization_code", "client_credentials", "refresh_token"]
)
```

### 注册路由

```python
from pancake.ovenware.web.security import register_oauth2_routes

register_oauth2_routes(app)  # 添加 /oauth/token, /oauth/introspect, /oauth/revoke
```

### 授权类型

**Authorization Code**（网页应用）：
```
POST /oauth/token
  grant_type=authorization_code&code=xxx&client_id=myapp&client_secret=secret&redirect_uri=...
```

**Client Credentials**（服务间调用）：
```
POST /oauth/token
  grant_type=client_credentials&client_id=myapp&client_secret=secret&scope=read
```

**Refresh Token**（刷新令牌）：
```
POST /oauth/token
  grant_type=refresh_token&refresh_token=xxx&client_id=myapp&client_secret=secret
```

### 保护路由

```python
@get_controller("/api/resource")
@oauth2_required(scopes=["read"])
async def get_resource(oauth_claims: dict):
    return {"user": oauth_claims.get("sub")}
```

### 内省令牌

```
POST /oauth/introspect
  token=xxx
```

### 撤销令牌

```
POST /oauth/revoke
  token=xxx
```

### 配置

```yaml
oauth2:
  secret: ${OAUTH2_SECRET}
  access_token_ttl: 3600
  refresh_token_ttl: 86400
  issuer: pancake
```

## 可选依赖

```bash
pip install bcrypt          # 更好的密码哈希
pip install argon2-cffi     # 最佳密码哈希
```

OAuth2 和会话管理无需额外依赖（使用内置 JWT 实现）。
