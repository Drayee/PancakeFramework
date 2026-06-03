# Redis 缓存

Redis 客户端，支持 Hash/List/Set 数据结构、JSON 存储、分布式锁和缓存防护。自动注入为 `redis_client`。

## 基础操作

```python
client = redis_client()  # 获取全局 Redis 客户端

await client.set("key", "value", ttl=300)
value = await client.get("key")
await client.delete("key")
exists = await client.exists("key")
await client.expire("key", 60)
await client.incr("counter")
await client.decr("counter")
```

## JSON 存储

```python
await client.set_json("user:1", {"name": "小明", "age": 30}, ttl=600)
data = await client.get_json("user:1")
```

## Hash 操作

```python
await client.hset("user:1", mapping={"name": "小明", "age": "30"})
name = await client.hget("user:1", "name")
all_fields = await client.hgetall("user:1")
await client.hdel("user:1", "age")
await client.hincrby("user:1", "visits", 1)
```

## List 操作

```python
await client.lpush("queue", "task1", "task2")
await client.rpush("queue", "task3")
item = await client.lpop("queue")
items = await client.lrange("queue", 0, -1)
length = await client.llen("queue")
```

## Set 操作

```python
await client.sadd("tags", "python", "web")
await client.srem("tags", "web")
members = await client.smembers("tags")
is_member = await client.sismember("tags", "python")
count = await client.scard("tags")
```

## 分布式锁

```python
lock = await client.lock("my_lock", timeout=10)
if lock:
    try:
        # 临界区
        ...
    finally:
        await lock.release()

# 或使用上下文管理器
async with await client.lock("my_lock") as lock:
    # 临界区
    ...
```

## 缓存防护 (CacheGuard)

三层防护，应对常见缓存问题：

```python
guard = CacheGuard(client)

# 防穿透：缓存空值 null_ttl 秒
# 防雪崩：TTL 加随机偏移
# 防击穿：单飞锁防止缓存击穿
result = await guard.get_or_load(
    "user:123",
    loader=lambda: db.query(123),
    ttl=600,
    null_ttl=30,
    jitter=60,
    protect_breakdown=True
)

# 手动失效
await guard.invalidate("user:123")
await guard.invalidate_pattern("user:*")
```

## @cached 装饰器

```python
@cached(ttl=300)
async def get_user(user_id: int):
    return await db.query(user_id)

@cached(key="user:{user_id}", ttl=600, jitter=60)
async def get_user_detail(user_id: int):
    return await db.query_detail(user_id)
```

## 配置

```yaml
redis:
  url: redis://localhost:6379
  db: 0
  password: ${REDIS_PASSWORD}
  key_prefix: "pancake:"
  default_ttl: 3600
```

## 可选依赖

```bash
pip install pancake_framework[redis]
```
