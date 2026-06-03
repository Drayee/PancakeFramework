# 远程调用

支持 HTTP REST 和 gRPC 协议的统一远程调用接口。

## @remote_node

```python
@remote_node(
    name="user_service",
    protocol="http",
    url="http://user-service:8080",
    endpoint="/api/users",
    timeout=30
)
async def get_users(page: int = 1):
    ...
```

参数作为请求体发送。响应存储在 langgraph 状态映射中。

## HTTP 远程调用

```python
from pancake.ovenware.remote import HttpRemote

client = HttpRemote(base_url="http://api.example.com", timeout=30)
result = await client.call("/users", method="GET")
result = await client.call("/users", method="POST", data={"name": "小明"})
result = await client.call("/users/1", method="PUT", data={"name": "小红"})
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `base_url` | 服务基础 URL | — |
| `timeout` | 请求超时（秒） | `30` |

## gRPC 远程调用

```python
from pancake.ovenware.remote import GrpcRemote

client = GrpcRemote(target="localhost:50051")
result = await client.call("UserService", "GetUser", {"id": 1})
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `target` | gRPC 服务器地址 | `localhost:50051` |

## RemoteProxy

管理多个远程客户端：

```python
from pancake.ovenware.remote import proxy

# 获取或创建 HTTP 客户端
http_client = proxy.get_http("http://service-a:8080", timeout=10)

# 获取或创建 gRPC 客户端
grpc_client = proxy.get_grpc("service-b:50051")

# 关闭所有连接
await proxy.close_all()
```

## 协议支持

| 协议 | 实现 | 依赖 |
|------|------|------|
| HTTP | `aiohttp` | 内置 |
| gRPC | `grpcio` | `pip install pancake_framework[grpc]` |

## 可选依赖

```bash
pip install pancake_framework[grpc]
```
