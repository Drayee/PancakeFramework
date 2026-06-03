# Remote Calls

HTTP REST and gRPC remote invocation with a unified interface.

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

Parameters are sent as the request body. The response is stored in the langgraph state map.

## HTTP Remote

```python
from pancake.ovenware.remote import HttpRemote

client = HttpRemote(base_url="http://api.example.com", timeout=30)
result = await client.call("/users", method="GET")
result = await client.call("/users", method="POST", data={"name": "Alice"})
result = await client.call("/users/1", method="PUT", data={"name": "Bob"})
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_url` | Service base URL | — |
| `timeout` | Request timeout (seconds) | `30` |

## gRPC Remote

```python
from pancake.ovenware.remote import GrpcRemote

client = GrpcRemote(target="localhost:50051")
result = await client.call("UserService", "GetUser", {"id": 1})
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `target` | gRPC server address | `localhost:50051` |

## RemoteProxy

Manages multiple remote clients:

```python
from pancake.ovenware.remote import proxy

# Get or create HTTP client
http_client = proxy.get_http("http://service-a:8080", timeout=10)

# Get or create gRPC client
grpc_client = proxy.get_grpc("service-b:50051")

# Close all connections
await proxy.close_all()
```

## Protocol Support

| Protocol | Implementation | Dependency |
|----------|---------------|------------|
| HTTP | `aiohttp` | Built-in |
| gRPC | `grpcio` | `pip install pancake_framework[grpc]` |

## Optional Dependency

```bash
pip install pancake_framework[grpc]
```
