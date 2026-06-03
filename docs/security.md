# Security

Built-in security features: password hashing, API key auth, CSRF protection, security headers, IP filtering, session management, and OAuth2 server.

## Password Hashing

Auto-detects best library: bcrypt > argon2 > hashlib (fallback).

```python
# Hash a password
hashed = hash_password("my-secret")

# Verify a password
is_valid = verify_password("my-secret", hashed)
```

Hash format is auto-detected on verify: `$2b$...` (bcrypt), `$argon2$...`, `$sha256$salt$hash`.

## API Key Authentication

```python
@get_controller("/api/data")
@api_key_required(keys=["secret-key-123"])
async def get_data():
    return {"data": "..."}
```

### Custom Validator

```python
async def validate_api_key(key: str) -> bool:
    return await db.exists("api_keys", key=key)

@get_controller("/api/data")
@api_key_required(validator=validate_api_key)
async def get_data():
    ...
```

### Custom Header

```python
@api_key_required(header="Authorization", keys=["Bearer my-key"])
async def get_data():
    ...
```

## Security Headers

Automatically adds security headers to all responses when enabled (default: on).

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Strict-Transport-Security | (optional, see config) |
| Content-Security-Policy | (optional, see config) |

### Configuration

```yaml
service:
  security_headers:
    enabled: true
    hsts: true
    csp: "default-src 'self'"
```

## IP Filtering

Whitelist or blacklist IPs with CIDR support.

```yaml
service:
  # Whitelist mode: only these IPs can access
  ip_whitelist:
    - "127.0.0.1"
    - "10.0.0.0/8"

  # Blacklist mode: these IPs are blocked
  ip_blacklist:
    - "192.168.1.100"
    - "10.0.0.0/24"
```

Whitelist takes priority over blacklist when both are configured.

## CSRF Protection

Protects POST/PUT/DELETE/PATCH requests. GET/HEAD/OPTIONS are exempt.

### Generate Token

```python
token = generate_csrf_token()
```

### Submit Token

Via form field:
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    ...
</form>
```

Or via header:
```javascript
fetch("/api/data", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken }
});
```

### Configuration

```yaml
service:
  csrf:
    enabled: true
    exempt_paths:
      - "/api/"       # API endpoints exempt from CSRF
      - "/webhook/"
```

## Session Management

Server-side sessions via cookie. Supports memory (default) and Redis backends.

```python
# Get session data
session = await get_session(request)

# In a route with manual session control
@post_controller("/login")
async def login(request: Request, username: str, password: str):
    session_mgr = SessionManager()
    session = await session_mgr.get_session(request)
    session["user_id"] = user.id
    response = JSONResponse({"status": "ok"})
    await session_mgr.save_session(request, response, session)
    return response
```

### Configuration

```yaml
service:
  session:
    backend: memory    # memory | redis
    ttl: 3600
    cookie_name: pancake_session
```

## OAuth2 Server

Full OAuth2 Authorization Server with JWT tokens.

### Register Client

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

### Register Routes

```python
from pancake.ovenware.web.security import register_oauth2_routes

register_oauth2_routes(app)  # Adds /oauth/token, /oauth/introspect, /oauth/revoke
```

### Grant Types

**Authorization Code** (web apps):
```
POST /oauth/token
  grant_type=authorization_code&code=xxx&client_id=myapp&client_secret=secret&redirect_uri=...
```

**Client Credentials** (service-to-service):
```
POST /oauth/token
  grant_type=client_credentials&client_id=myapp&client_secret=secret&scope=read
```

**Refresh Token**:
```
POST /oauth/token
  grant_type=refresh_token&refresh_token=xxx&client_id=myapp&client_secret=secret
```

### Protect Routes

```python
@get_controller("/api/resource")
@oauth2_required(scopes=["read"])
async def get_resource(oauth_claims: dict):
    return {"user": oauth_claims.get("sub")}
```

### Introspect Token

```
POST /oauth/introspect
  token=xxx
```

### Revoke Token

```
POST /oauth/revoke
  token=xxx
```

### Configuration

```yaml
oauth2:
  secret: ${OAUTH2_SECRET}
  access_token_ttl: 3600
  refresh_token_ttl: 86400
  issuer: pancake
```

## Optional Dependencies

```bash
pip install bcrypt          # Better password hashing
pip install argon2-cffi     # Best password hashing
```

OAuth2 and session management work without extra dependencies (uses built-in JWT implementation).
