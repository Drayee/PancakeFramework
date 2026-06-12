# 15. Remote 插件 — 远程调用

[← 上一节](14-langgraph.md) | [下一节 →](16-cui.md)

---

## 概述

`pancake-remote` 提供 HTTP 和 gRPC 远程调用客户端。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>remote</artifactId>
</dependency>
```

## HTTP 远程调用

```python
# 创建客户端
api = HttpRemote(base_url="https://api.example.com", timeout=30)

# GET 请求
users = await api.call("/users", method="GET")

# POST 请求
result = await api.call("/users", method="POST", data={"name": "Alice"})

# 关闭连接
await api.close()
```

## gRPC 远程调用

```python
grpc_client = GrpcRemote(host="localhost", port=50051)
result = await grpc_client.call("UserService", "GetUser", {"user_id": 1})
```

## @remote_node 装饰器

```python
@remote_node(base_url="https://api.example.com")
async def fetch_user(user_id: int, remote: HttpRemote):
    return await remote.call(f"/users/{user_id}", method="GET")
```

---

[← 上一节](14-langgraph.md) | [下一节 →](16-cui.md)
