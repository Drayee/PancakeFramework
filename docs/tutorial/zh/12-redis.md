# 12. Redis 插件 — 缓存

[← 上一节](11-ai.md) | [下一节 →](13-messaging.md)

---

## 概述

`pancake-redis` 提供 Redis 缓存集成，支持基础缓存操作、Hash/List/Set 数据结构、`@cached` 装饰器、CacheGuard 防穿透/雪崩/击穿。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>redis</artifactId>
</dependency>
```

## 配置

```yaml
redis:
  url: redis://localhost:6379
  db: 0
  password: null
  key_prefix: "pancake:"
  default_ttl: 3600
```

## 基本操作

```python
# 获取 Redis 客户端
client = redis_client

# 基础缓存
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

## @cached 装饰器

```python
@cached(ttl=300, key_prefix="user")
async def get_user(user_id: int):
    # 结果自动缓存 300 秒
    return await user_mapper.select_by_id(user_id)
```

## CacheGuard — 防穿透/雪崩/击穿

```python
guard = CacheGuard(
    redis_client=redis_client,
    ttl=3600,
    null_ttl=60,           # 空值缓存时间（防穿透）
    lock_ttl=10,            # 分布式锁时间（防击穿）
    jitter_range=(0, 300),  # TTL 随机抖动范围（防雪崩）
)

# 使用
user = await guard.get_or_load(
    key="user:1",
    loader=lambda: user_mapper.select_by_id(1)
)
```

| 问题 | 策略 | CacheGuard 参数 |
|------|------|----------------|
| 缓存穿透 | 缓存空值 | `null_ttl` |
| 缓存雪崩 | TTL 随机抖动 | `jitter_range` |
| 缓存击穿 | 分布式锁 | `lock_ttl` |

---

[← 上一节](11-ai.md) | [下一节 →](13-messaging.md)
