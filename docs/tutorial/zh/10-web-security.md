# 10. Web Security 插件 — 安全

[← 上一节](09-web-template.md) | [下一节 →](11-ai.md)

---

## 概述

`pancake-web-security` 提供 Spring Security 风格的认证和授权，支持 Form 登录、JWT、CSRF 防护、限流、安全响应头。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-security</artifactId>
</dependency>
```

## 配置

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

## 认证

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

## 授权装饰器

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

## 密码加密

```python
# 自动注入
password_encoder: PasswordEncoder

# 使用
hashed = password_encoder.encode("my_password")
is_valid = password_encoder.matches("my_password", hashed)
```

## 核心类

| 类 | 说明 |
|----|------|
| `Authentication` | 认证信息 |
| `SecurityContextHolder` | 安全上下文 |
| `User` | 用户模型 |
| `Role` | 角色 |
| `Permission` | 权限 |
| `AuthenticationManager` | 认证管理器 |
| `PasswordEncoder` | 密码编码器 |

---

[← 上一节](09-web-template.md) | [下一节 →](11-ai.md)
