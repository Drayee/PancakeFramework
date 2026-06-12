# 15. Remote Plugin — RPC

[← Previous](14-langgraph.md) | [Next →](16-cui.md)

---

## Overview

`pancake-remote` provides HTTP and gRPC remote call clients.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>remote</artifactId>
</dependency>
```

## HTTP Remote Calls

```python
# Create client
api = HttpRemote(base_url="https://api.example.com", timeout=30)

# GET request
users = await api.call("/users", method="GET")

# POST request
result = await api.call("/users", method="POST", data={"name": "Alice"})

# Close connection
await api.close()
```

## gRPC Remote Calls

```python
grpc_client = GrpcRemote(host="localhost", port=50051)
result = await grpc_client.call("UserService", "GetUser", {"user_id": 1})
```

## @remote_node Decorator

```python
@remote_node(base_url="https://api.example.com")
async def fetch_user(user_id: int, remote: HttpRemote):
    return await remote.call(f"/users/{user_id}", method="GET")
```

---

[← Previous](14-langgraph.md) | [Next →](16-cui.md)
