"""
安全模块
提供密码哈希、API Key 认证、CSRF 防护、安全响应头、IP 过滤、会话管理、OAuth2 服务

所有功能通过 __init__.py re-export 并注册到 builtins
"""

import asyncio
import base64
import functools
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import time
from typing import Any, Callable
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse, Response

from .filter import Filter

logger = logging.getLogger(__name__)


# ============================================================
#  1. Password Hashing — 密码哈希
# ============================================================

def _detect_hasher():
    """检测可用的哈希库: bcrypt > argon2 > hashlib"""
    try:
        import bcrypt
        return "bcrypt"
    except ImportError:
        pass
    try:
        from argon2 import PasswordHasher
        return "argon2"
    except ImportError:
        pass
    return "hashlib"


_HASHER = _detect_hasher()


def hash_password(password: str) -> str:
    """
    哈希密码，返回存储格式字符串

    自动选择最佳算法: bcrypt > argon2 > hashlib
    返回格式: "$bcrypt$...", "$argon2$...", "$sha256$salt$hash"
    """
    if _HASHER == "bcrypt":
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    if _HASHER == "argon2":
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        return ph.hash(password)

    # hashlib 回退: sha256 + random salt
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"$sha256${salt}${h}"


def verify_password(password: str, hashed: str) -> bool:
    """
    验证密码是否匹配哈希值

    支持 bcrypt、argon2、sha256 三种格式
    """
    if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())

    if hashed.startswith("$argon2"):
        try:
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            return ph.verify(hashed, password)
        except Exception:
            return False

    if hashed.startswith("$sha256$"):
        parts = hashed.split("$")
        if len(parts) != 4:
            return False
        salt = parts[2]
        expected = parts[3]
        actual = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(expected, actual)

    return False


# ============================================================
#  2. Security Headers — 安全响应头
# ============================================================

class SecurityHeadersFilter(Filter):
    """
    内置安全响应头 Filter

    自动添加常见安全头:
      X-Content-Type-Options: nosniff
      X-Frame-Options: DENY
      X-XSS-Protection: 1; mode=block
      Referrer-Policy: strict-origin-when-cross-origin
      Strict-Transport-Security (可选)
      Content-Security-Policy (可选)

    配置 (YAML):
      service.security_headers.enabled: true
      service.security_headers.hsts: true
      service.security_headers.csp: "default-src 'self'"
    """
    order = 10
    name = "security_headers"

    def __init__(self):
        from pancake import oven
        self.enabled = True
        self.hsts = False
        self.csp = None

        config = oven.pancake_yaml
        if "service.security_headers.enabled" in config:
            self.enabled = config["service.security_headers.enabled"] in (True, "true", "1")
        if "service.security_headers.hsts" in config:
            self.hsts = config["service.security_headers.hsts"] in (True, "true", "1")
        if "service.security_headers.csp" in config:
            self.csp = config["service.security_headers.csp"]

    async def do_filter(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if not self.enabled:
            return response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if self.hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if self.csp:
            response.headers["Content-Security-Policy"] = self.csp
        return response


# ============================================================
#  3. IP Filter — IP 黑白名单
# ============================================================

class IPFilter(Filter):
    """
    IP 过滤 Filter — 支持 CIDR 格式的黑白名单

    配置 (YAML):
      service.ip_whitelist: ["127.0.0.1", "10.0.0.0/8"]
      service.ip_blacklist: ["192.168.1.100"]

    白名单模式: 只允许列表中的 IP 访问
    黑名单模式: 拒绝列表中的 IP（默认）
    两者同时配置时，白名单优先
    """
    order = 5
    name = "ip_filter"

    def __init__(self):
        from pancake import oven
        self._whitelist: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        self._blacklist: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

        config = oven.pancake_yaml
        wl = config.get("service.ip_whitelist")
        if wl and isinstance(wl, list):
            for entry in wl:
                try:
                    self._whitelist.append(ipaddress.ip_network(entry, strict=False))
                except ValueError:
                    logger.warning(f"IP 白名单格式错误: {entry}")

        bl = config.get("service.ip_blacklist")
        if bl and isinstance(bl, list):
            for entry in bl:
                try:
                    self._blacklist.append(ipaddress.ip_network(entry, strict=False))
                except ValueError:
                    logger.warning(f"IP 黑名单格式错误: {entry}")

    def _is_in_networks(self, ip_str: str, networks) -> bool:
        try:
            addr = ipaddress.ip_address(ip_str)
            return any(addr in net for net in networks)
        except ValueError:
            return False

    async def do_filter(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        if self._whitelist:
            if not self._is_in_networks(client_ip, self._whitelist):
                return JSONResponse(status_code=403, content={"detail": "IP 不在白名单中"})
        elif self._blacklist:
            if self._is_in_networks(client_ip, self._blacklist):
                return JSONResponse(status_code=403, content={"detail": "IP 已被封禁"})

        return await call_next(request)


# ============================================================
#  4. API Key 认证
# ============================================================

def api_key_required(header: str = "X-API-Key", keys: list[str] = None,
                     validator: Callable = None):
    """
    API Key 认证装饰器

    用法:
        @get_controller("/api/data")
        @api_key_required(keys=["secret-key-123"])
        async def get_data():
            ...

        # 自定义验证器
        @get_controller("/api/data")
        @api_key_required(validator=async def(key) -> bool: return key in db)
        async def get_data():
            ...

    Args:
        header: 从哪个 header 读取 key
        keys: 允许的 key 列表（静态）
        validator: 自定义验证函数 async def(key) -> bool
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            key = request.headers.get(header)
            if not key:
                raise HTTPException(status_code=401, detail=f"缺少 {header} 头")

            if validator:
                if asyncio.iscoroutinefunction(validator):
                    valid = await validator(key)
                else:
                    valid = validator(key)
                if not valid:
                    raise HTTPException(status_code=401, detail="API Key 无效")
            elif keys:
                if key not in keys:
                    raise HTTPException(status_code=401, detail="API Key 无效")
            else:
                raise HTTPException(status_code=500, detail="api_key_required 未配置 keys 或 validator")

            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


# ============================================================
#  5. CSRF 防护
# ============================================================

_csrf_tokens: dict[str, float] = {}  # token -> expiry


def generate_csrf_token(session_id: str = None, ttl: int = 3600) -> str:
    """
    生成 CSRF 令牌

    Args:
        session_id: 可选，绑定到会话 ID
        ttl: 过期时间（秒）

    Returns:
        CSRF 令牌字符串
    """
    token = secrets.token_urlsafe(32)
    _csrf_tokens[token] = time.time() + ttl
    # 清理过期 token
    now = time.time()
    expired = [t for t, exp in _csrf_tokens.items() if exp < now]
    for t in expired:
        _csrf_tokens.pop(t, None)
    return token


def _verify_csrf_token(token: str) -> bool:
    """验证 CSRF 令牌"""
    if not token:
        return False
    expiry = _csrf_tokens.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _csrf_tokens.pop(token, None)
        return False
    # 一次性：验证后删除
    _csrf_tokens.pop(token, None)
    return True


class CSRFProtectFilter(Filter):
    """
    CSRF 防护 Filter

    GET/HEAD/OPTIONS 自动豁免。
    POST/PUT/DELETE/PATCH 需要通过以下方式之一提交 CSRF 令牌:
      - 表单字段: csrf_token
      - Header: X-CSRF-Token

    配置 (YAML):
      service.csrf.enabled: true
      service.csrf.exempt_paths: ["/api/"]
    """
    order = 15
    name = "csrf_protect"

    def __init__(self):
        from pancake import oven
        self.enabled = True
        self.exempt_paths: list[str] = []

        config = oven.pancake_yaml
        if "service.csrf.enabled" in config:
            self.enabled = config["service.csrf.enabled"] in (True, "true", "1")
        if "service.csrf.exempt_paths" in config:
            paths = config["service.csrf.exempt_paths"]
            if isinstance(paths, list):
                self.exempt_paths = paths

    async def do_filter(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        # 安全方法豁免
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # 路径豁免
        path = request.url.path
        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return await call_next(request)

        # 从 header 或 form 获取 token
        token = request.headers.get("X-CSRF-Token")
        if not token:
            try:
                form = await request.form()
                token = form.get("csrf_token")
            except Exception:
                pass

        if not _verify_csrf_token(token):
            return JSONResponse(status_code=403, content={"detail": "CSRF 令牌无效或已过期"})

        return await call_next(request)


# ============================================================
#  6. Session 管理
# ============================================================

class _MemorySessionStore:
    """内存会话存储"""

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._expiry: dict[str, float] = {}

    async def get(self, session_id: str) -> dict | None:
        exp = self._expiry.get(session_id)
        if exp and time.time() > exp:
            self._store.pop(session_id, None)
            self._expiry.pop(session_id, None)
            return None
        return self._store.get(session_id)

    async def set(self, session_id: str, data: dict, ttl: int = 3600):
        self._store[session_id] = data
        self._expiry[session_id] = time.time() + ttl

    async def delete(self, session_id: str):
        self._store.pop(session_id, None)
        self._expiry.pop(session_id, None)


class _RedisSessionStore:
    """Redis 会话存储"""

    def __init__(self, redis_client):
        self._client = redis_client
        self._prefix = "session:"

    async def get(self, session_id: str) -> dict | None:
        data = await self._client.get_json(f"{self._prefix}{session_id}")
        return data

    async def set(self, session_id: str, data: dict, ttl: int = 3600):
        await self._client.set_json(f"{self._prefix}{session_id}", data, ttl=ttl)

    async def delete(self, session_id: str):
        await self._client.delete(f"{self._prefix}{session_id}")


class SessionManager:
    """
    会话管理器

    通过 cookie (pancake_session) 传递 session_id。
    支持 memory（默认）和 redis 后端。

    配置 (YAML):
      service.session.backend: memory   # memory | redis
      service.session.ttl: 3600
      service.session.cookie_name: pancake_session
    """

    def __init__(self):
        from pancake import oven
        self.ttl = int(oven.pancake_yaml.get("service.session.ttl", 3600))
        self.cookie_name = oven.pancake_yaml.get("service.session.cookie_name", "pancake_session")

        backend = oven.pancake_yaml.get("service.session.backend", "memory")
        if backend == "redis":
            from .redis_cache import get_client
            client = get_client()
            if client:
                self._store = _RedisSessionStore(client)
                logger.info("Session 后端: Redis")
            else:
                logger.warning("Redis 未初始化，回退到内存 Session")
                self._store = _MemorySessionStore()
        else:
            self._store = _MemorySessionStore()
            logger.info("Session 后端: Memory")

    async def get_session(self, request: Request) -> dict:
        """获取或创建会话"""
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            data = await self._store.get(session_id)
            if data is not None:
                return data
        return {}

    async def save_session(self, request: Request, response: Response, data: dict):
        """保存会话并设置 cookie"""
        session_id = request.cookies.get(self.cookie_name)
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        await self._store.set(session_id, data, ttl=self.ttl)
        response.set_cookie(self.cookie_name, session_id, max_age=self.ttl, httponly=True)

    async def destroy_session(self, request: Request, response: Response):
        """销毁会话"""
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            await self._store.delete(session_id)
        response.delete_cookie(self.cookie_name)


# 全局会话管理器
_session_manager: SessionManager | None = None


def _get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def get_session(request: Request) -> dict:
    """FastAPI 依赖：获取当前会话数据"""
    return await _get_session_manager().get_session(request)


# ============================================================
#  7. OAuth2 服务器
# ============================================================

def _jwt_encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """简单 JWT 编码（不依赖第三方库）"""
    header = base64.urlsafe_b64encode(json.dumps({"alg": algorithm, "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    signing_input = f"{header}.{body}"
    if algorithm == "HS256":
        sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    else:
        raise ValueError(f"不支持的算法: {algorithm}")
    signature = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{body}.{signature}"


def _jwt_decode(token: str, secret: str, algorithm: str = "HS256") -> dict:
    """简单 JWT 解码"""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("无效的 JWT 格式")

    header, body, signature = parts
    signing_input = f"{header}.{body}"

    if algorithm == "HS256":
        expected = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    else:
        raise ValueError(f"不支持的算法: {algorithm}")

    expected_sig = base64.urlsafe_b64encode(expected).rstrip(b"=").decode()
    if not hmac.compare_digest(signature, expected_sig):
        raise ValueError("JWT 签名无效")

    # 补齐 base64 padding
    padded = body + "=" * (4 - len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))

    # 检查过期
    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("JWT 已过期")

    return payload


class OAuth2Client:
    """OAuth2 客户端注册信息"""
    def __init__(self, client_id: str, client_secret: str,
                 redirect_uris: list[str], scopes: list[str] = None,
                 grant_types: list[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uris = redirect_uris
        self.scopes = scopes or ["read"]
        self.grant_types = grant_types or ["authorization_code", "refresh_token"]


class OAuth2Server:
    """
    OAuth2 授权服务器

    支持:
      - Authorization Code Grant（网页应用）
      - Client Credentials Grant（服务间调用）
      - Refresh Token Grant（刷新令牌）
      - Token Introspection
      - Token Revocation

    配置 (YAML):
      oauth2.secret: "your-secret-key"
      oauth2.access_token_ttl: 3600
      oauth2.refresh_token_ttl: 86400
      oauth2.issuer: "pancake"

    用法:
        server = OAuth2Server()
        server.register_client("myapp", "secret", ["http://localhost:8080/callback"])
    """

    def __init__(self):
        from pancake import oven
        self.secret = oven.pancake_yaml.get("oauth2.secret", secrets.token_hex(32))
        self.access_token_ttl = int(oven.pancake_yaml.get("oauth2.access_token_ttl", 3600))
        self.refresh_token_ttl = int(oven.pancake_yaml.get("oauth2.refresh_token_ttl", 86400))
        self.issuer = oven.pancake_yaml.get("oauth2.issuer", "pancake")

        self._clients: dict[str, OAuth2Client] = {}
        self._auth_codes: dict[str, dict] = {}  # code -> {client_id, redirect_uri, scope, user, exp}
        self._refresh_tokens: dict[str, dict] = {}  # token -> {client_id, scope, user, exp}

    def register_client(self, client_id: str, client_secret: str,
                        redirect_uris: list[str], scopes: list[str] = None,
                        grant_types: list[str] = None):
        """注册 OAuth2 客户端"""
        self._clients[client_id] = OAuth2Client(
            client_id, client_secret, redirect_uris, scopes, grant_types
        )
        logger.info(f"OAuth2 客户端已注册: {client_id}")

    def _get_client(self, client_id: str) -> OAuth2Client | None:
        return self._clients.get(client_id)

    def _verify_client(self, client_id: str, client_secret: str) -> OAuth2Client | None:
        client = self._get_client(client_id)
        if client and client.client_secret == client_secret:
            return client
        return None

    async def authorize(self, client_id: str, redirect_uri: str,
                        scope: str, state: str, response_type: str,
                        user: Any = None) -> str:
        """
        授权端点 — 生成授权码

        Args:
            client_id: 客户端 ID
            redirect_uri: 回调地址
            scope: 请求的权限范围
            state: 防 CSRF 状态参数
            response_type: 必须为 "code"
            user: 当前认证用户

        Returns:
            重定向 URL（带 code 和 state）
        """
        client = self._get_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="无效的 client_id")

        if redirect_uri not in client.redirect_uris:
            raise HTTPException(status_code=400, detail="无效的 redirect_uri")

        if response_type != "code":
            raise HTTPException(status_code=400, detail="不支持的 response_type")

        # 生成授权码
        code = secrets.token_urlsafe(32)
        self._auth_codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "user": user,
            "exp": time.time() + 600,  # 10 分钟有效
        }

        # 构建回调 URL
        separator = "&" if "?" in redirect_uri else "?"
        return f"{redirect_uri}{separator}code={code}&state={state}"

    async def exchange_code(self, client_id: str, client_secret: str,
                            code: str, redirect_uri: str) -> dict:
        """
        令牌端点 — 用授权码换令牌

        Returns:
            {"access_token": "...", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "..."}
        """
        client = self._verify_client(client_id, client_secret)
        if not client:
            raise HTTPException(status_code=401, detail="客户端认证失败")

        code_data = self._auth_codes.pop(code, None)
        if not code_data:
            raise HTTPException(status_code=400, detail="无效的授权码")

        if time.time() > code_data["exp"]:
            raise HTTPException(status_code=400, detail="授权码已过期")

        if code_data["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="client_id 不匹配")

        if code_data["redirect_uri"] != redirect_uri:
            raise HTTPException(status_code=400, detail="redirect_uri 不匹配")

        return self._issue_tokens(client_id, code_data["scope"], code_data["user"])

    async def client_credentials_grant(self, client_id: str, client_secret: str,
                                        scope: str = "") -> dict:
        """
        Client Credentials Grant — 服务间调用

        Returns:
            {"access_token": "...", "token_type": "Bearer", "expires_in": 3600}
        """
        client = self._verify_client(client_id, client_secret)
        if not client:
            raise HTTPException(status_code=401, detail="客户端认证失败")

        if "client_credentials" not in client.grant_types:
            raise HTTPException(status_code=400, detail="不支持 client_credentials 授权类型")

        return self._issue_tokens(client_id, scope, user=None, include_refresh=False)

    async def refresh_grant(self, client_id: str, client_secret: str,
                            refresh_token: str) -> dict:
        """
        Refresh Token Grant — 刷新访问令牌

        Returns:
            {"access_token": "...", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "..."}
        """
        client = self._verify_client(client_id, client_secret)
        if not client:
            raise HTTPException(status_code=401, detail="客户端认证失败")

        token_data = self._refresh_tokens.get(refresh_token)
        if not token_data:
            raise HTTPException(status_code=400, detail="无效的 refresh_token")

        if time.time() > token_data["exp"]:
            self._refresh_tokens.pop(refresh_token, None)
            raise HTTPException(status_code=400, detail="refresh_token 已过期")

        if token_data["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="client_id 不匹配")

        # 删除旧 refresh_token（rotation）
        self._refresh_tokens.pop(refresh_token, None)

        return self._issue_tokens(client_id, token_data["scope"], token_data["user"])

    async def introspect(self, token: str) -> dict:
        """
        Token Introspection — 验证令牌状态

        Returns:
            {"active": true, "scope": "...", "client_id": "...", "exp": ...} 或 {"active": false}
        """
        try:
            payload = _jwt_decode(token, self.secret)
            return {
                "active": True,
                "scope": payload.get("scope", ""),
                "client_id": payload.get("client_id"),
                "username": payload.get("sub"),
                "exp": payload.get("exp"),
                "iss": payload.get("iss"),
                "token_type": "access_token",
            }
        except Exception:
            return {"active": False}

    async def revoke(self, token: str) -> None:
        """撤销令牌"""
        # 撤销 refresh_token
        self._refresh_tokens.pop(token, None)
        # JWT access_token 无法真正撤销（stateless），但可以从 refresh_token 存储中删除

    def _issue_tokens(self, client_id: str, scope: str, user: Any = None,
                      include_refresh: bool = True) -> dict:
        """签发 access_token 和可选的 refresh_token"""
        now = time.time()

        # Access Token
        access_payload = {
            "iss": self.issuer,
            "client_id": client_id,
            "scope": scope,
            "iat": now,
            "exp": int(now + self.access_token_ttl),
        }
        if user:
            access_payload["sub"] = str(user) if not isinstance(user, dict) else user.get("id", str(user))

        access_token = _jwt_encode(access_payload, self.secret)

        result = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
        }

        # Refresh Token
        if include_refresh:
            refresh_token = secrets.token_urlsafe(32)
            self._refresh_tokens[refresh_token] = {
                "client_id": client_id,
                "scope": scope,
                "user": user,
                "exp": int(now + self.refresh_token_ttl),
            }
            result["refresh_token"] = refresh_token

        return result


class OAuth2ResourceServer:
    """
    OAuth2 资源服务器 — 验证 Bearer Token

    用法:
        resource_server = OAuth2ResourceServer(required_scopes=["read"])
        claims = await resource_server.verify(request)
    """

    def __init__(self, server: OAuth2Server, required_scopes: list[str] = None):
        self.server = server
        self.required_scopes = required_scopes or []

    async def verify(self, request: Request) -> dict:
        """
        验证 Bearer Token 并返回 claims

        Raises:
            HTTPException(401): token 无效或过期
            HTTPException(403): scope 不足
        """
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="缺少 Bearer token")

        token = auth[7:]
        result = await self.server.introspect(token)

        if not result.get("active"):
            raise HTTPException(status_code=401, detail="令牌无效或已过期")

        # 检查 scope
        if self.required_scopes:
            token_scopes = result.get("scope", "").split()
            for required in self.required_scopes:
                if required not in token_scopes:
                    raise HTTPException(status_code=403, detail=f"权限不足，需要 scope: {required}")

        return result


# 全局 OAuth2 服务器实例
_oauth2_server: OAuth2Server | None = None


def _get_oauth2_server() -> OAuth2Server:
    global _oauth2_server
    if _oauth2_server is None:
        _oauth2_server = OAuth2Server()
    return _oauth2_server


def oauth2_required(scopes: list[str] = None):
    """
    OAuth2 认证装饰器 — 验证 Bearer Token 和 scope

    用法:
        @get_controller("/api/resource")
        @oauth2_required(scopes=["read"])
        async def get_resource():
            ...

        @post_controller("/api/resource")
        @oauth2_required(scopes=["write"])
        async def create_resource():
            ...
    """
    server = _get_oauth2_server()
    resource_server = OAuth2ResourceServer(server, required_scopes=scopes)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            claims = await resource_server.verify(request)
            kwargs["oauth_claims"] = claims
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


# ============================================================
#  OAuth2 授权端点路由辅助
# ============================================================

def register_oauth2_routes(app, server: OAuth2Server = None):
    """
    注册 OAuth2 标准路由

    POST /oauth/token      — 令牌端点
    POST /oauth/introspect — 令牌内省
    POST /oauth/revoke     — 令牌撤销
    GET  /oauth/authorize  — 授权端点（需要配合认证）

    用法:
        from pancake.ovenware.web.security import register_oauth2_routes
        register_oauth2_routes(app)
    """
    if server is None:
        server = _get_oauth2_server()

    @app.post("/oauth/token")
    async def token_endpoint(request: Request):
        form = await request.form()
        grant_type = form.get("grant_type")

        if grant_type == "authorization_code":
            return await server.exchange_code(
                client_id=form.get("client_id"),
                client_secret=form.get("client_secret"),
                code=form.get("code"),
                redirect_uri=form.get("redirect_uri"),
            )
        elif grant_type == "client_credentials":
            return await server.client_credentials_grant(
                client_id=form.get("client_id"),
                client_secret=form.get("client_secret"),
                scope=form.get("scope", ""),
            )
        elif grant_type == "refresh_token":
            return await server.refresh_grant(
                client_id=form.get("client_id"),
                client_secret=form.get("client_secret"),
                refresh_token=form.get("refresh_token"),
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 grant_type: {grant_type}")

    @app.post("/oauth/introspect")
    async def introspect_endpoint(request: Request):
        form = await request.form()
        token = form.get("token")
        return await server.introspect(token)

    @app.post("/oauth/revoke")
    async def revoke_endpoint(request: Request):
        form = await request.form()
        token = form.get("token")
        await server.revoke(token)
        return {"status": "ok"}
