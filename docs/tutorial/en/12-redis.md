# 12. Redis Plugin — Cache

[← Previous](11-ai.md) | [Next →](13-messaging.md)

---

## Overview

`pancake-redis` provides Redis cache integration with basic operations, Hash/List/Set data structures, `@cached` decorator, and CacheGuard (anti-penetration/avalanche/breakdown).

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>redis</artifactId>
</dependency>
```

## Configuration

```yaml
redis:
  url: redis://localhost:6379
  db: 0
  password: null
  key_prefix: "pancake:"
  default_ttl: 3600
```

## Basic Operations

```python
# Get Redis client
client = redis_client

# Basic cache
await client.set("user:1", {"name": "Alice", "age": 25}, ttl=3600)
user = await client.get("user:1")
await client.delete("user:1")

# Hash
await client.hset("user:1", "name", "Alice")
name = await client.hget("user:1", "name")
all_fields = await client.hgetall("user:1")

# List
await client.lpush("queue", "task1", "task2")
task = await client.rpop("queue")

# Set
await client.sadd("tags", "python", "pancake")
members = await client.smembers("tags")
```

## @cached Decorator

```python
@cached(ttl=300, key_prefix="user")
async def get_user(user_id: int):
    # Result auto-cached for 300 seconds
    return await user_mapper.select_by_id(user_id)
```

## CacheGuard — Anti-Penetration/Avalanche/Breakdown

```python
guard = CacheGuard(
    redis_client=redis_client,
    ttl=3600,
    null_ttl=60,           # Null value cache time (anti-penetration)
    lock_ttl=10,            # Distributed lock time (anti-breakdown)
    jitter_range=(0, 300),  # TTL random jitter range (anti-avalanche)
)

# Usage
user = await guard.get_or_load(
    key="user:1",
    loader=lambda: user_mapper.select_by_id(1)
)
```

| Problem | Strategy | CacheGuard Param |
|---------|----------|-----------------|
| Cache penetration | Cache null values | `null_ttl` |
| Cache avalanche | TTL random jitter | `jitter_range` |
| Cache breakdown | Distributed lock | `lock_ttl` |

---

[← Previous](11-ai.md) | [Next →](13-messaging.md)
