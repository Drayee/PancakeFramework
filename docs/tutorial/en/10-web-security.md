# 10. Web Security Plugin — Security

[← Previous](09-web-template.md) | [Next →](11-ai.md)

---

## Overview

`pancake-web-security` provides Spring Security-style authentication and authorization, supporting Form login, JWT, CSRF protection, rate limiting, and security headers.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-security</artifactId>
</dependency>
```

## Configuration

```yaml
# src/resource/yaml/security.yaml
security:
  enabled: true
  auth_type: both          # form | jwt | both
  password_encoder: bcrypt # bcrypt | argon2 | plain
  bcrypt_rounds: 12
  memory_users:
    - username: admin
      password: admin123
      roles: [ADMIN]
    - username: user
      password: user123
      roles: [USER]
  jwt:
    secret: your-jwt-secret
    expire: 3600
    header: Authorization
    prefix: Bearer
```

## Authentication

```python
@controller("/auth")
class AuthController:
    @post("/login")
    async def login(self, body: dict = request_body()):
        auth = await auth_manager.authenticate(
            username=body["username"],
            password=body["password"]
        )
        return {"token": auth.token, "user": auth.principal.username}

    @get("/me")
    @has_role("USER")
    async def me(self, user: User = authenticated_user()):
        return {"username": user.username, "roles": user.roles}
```

## Authorization Decorators

```python
@get("/admin/dashboard")
@has_role("ADMIN")
async def admin_dashboard(self, request):
    return {"message": "Admin Dashboard"}

@get("/users/delete")
@has_permission("user:delete")
async def delete_user(self, request):
    return {"message": "User deleted"}

@get("/protected")
@secured(roles=["ADMIN", "MODERATOR"], permissions=["access:protected"])
async def protected_resource(self, request):
    return {"message": "Protected"}
```

## Password Encoding

```python
# Auto-injected
password_encoder: PasswordEncoder

# Usage
hashed = password_encoder.encode("my_password")
is_valid = password_encoder.matches("my_password", hashed)
```

## Core Classes

| Class | Description |
|-------|-------------|
| `Authentication` | Authentication info |
| `SecurityContextHolder` | Security context |
| `User` | User model |
| `Role` | Role |
| `Permission` | Permission |
| `AuthenticationManager` | Authentication manager |
| `PasswordEncoder` | Password encoder |

---

[← Previous](09-web-template.md) | [Next →](11-ai.md)
