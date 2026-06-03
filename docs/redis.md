# Redis Cache

Redis client with Hash/List/Set data structures, JSON storage, distributed locks, and cache protection. Auto-injected as `redis_client`.

## Basic Operations

```python
client = redis_client()  # Get global Redis client

await client.set("key", "value", ttl=300)
value = await client.get("key")
await client.delete("key")
exists = await client.exists("key")
await client.expire("key", 60)
await client.incr("counter")
await client.decr("counter")
```

## JSON Storage

```python
await client.set_json("user:1", {"name": "Alice", "age": 30}, ttl=600)
data = await client.get_json("user:1")
```

## Hash Operations

```python
await client.hset("user:1", mapping={"name": "Alice", "age": "30"})
name = await client.hget("user:1", "name")
all_fields = await client.hgetall("user:1")
await client.hdel("user:1", "age")
await client.hincrby("user:1", "visits", 1)
```

## List Operations

```python
await client.lpush("queue", "task1", "task2")
await client.rpush("queue", "task3")
item = await client.lpop("queue")
items = await client.lrange("queue", 0, -1)
length = await client.llen("queue")
```

## Set Operations

```python
await client.sadd("tags", "python", "web")
await client.srem("tags", "web")
members = await client.smembers("tags")
is_member = await client.sismember("tags", "python")
count = await client.scard("tags")
```

## Distributed Lock

```python
lock = await client.lock("my_lock", timeout=10)
if lock:
    try:
        # Critical section
        ...
    finally:
        await lock.release()

# Or use as context manager
async with await client.lock("my_lock") as lock:
    # Critical section
    ...
```

## Cache Protection (CacheGuard)

Three-layer protection against common cache problems:

```python
guard = CacheGuard(client)

# Anti-penetration: caches null values for null_ttl seconds
# Anti-avalanche: adds random jitter to TTL
# Anti-breakdown: singleflight lock prevents thundering herd
result = await guard.get_or_load(
    "user:123",
    loader=lambda: db.query(123),
    ttl=600,
    null_ttl=30,
    jitter=60,
    protect_breakdown=True
)

# Manual invalidation
await guard.invalidate("user:123")
await guard.invalidate_pattern("user:*")
```

## @cached Decorator

```python
@cached(ttl=300)
async def get_user(user_id: int):
    return await db.query(user_id)

@cached(key="user:{user_id}", ttl=600, jitter=60)
async def get_user_detail(user_id: int):
    return await db.query_detail(user_id)
```

## Configuration

```yaml
redis:
  url: redis://localhost:6379
  db: 0
  password: ${REDIS_PASSWORD}
  key_prefix: "pancake:"
  default_ttl: 3600
```

## Optional Dependency

```bash
pip install pancake_framework[redis]
```
