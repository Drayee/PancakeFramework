# 消息队列

基于事件驱动的消息系统，支持内存和 Redis 两种代理。

## @event_node

函数完成时发布事件：

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}
```

函数结果自动发布到指定事件主题。

## @on_event

订阅事件：

```python
@on_event("order.created")
async def notify_inventory(message):
    print(f"收到订单: {message}")

@on_event("order.created")
async def send_confirmation(message):
    await email.send(message["data"])
```

## 消息代理

### SimpleBroker（默认）

内存消息队列，无外部依赖。

- 消息在同一进程内同步传递
- `@on_event` 注册的处理器在首次 publish 时自动订阅

### RedisBroker

基于 Redis Pub/Sub，需要 Redis。

```python
from pancake.ovenware.broker import RedisBroker, set_broker

set_broker(RedisBroker(url="redis://localhost:6379"))
```

特性：
- 跨进程消息传递
- 指数退避重试
- 自动重连

## 编程使用

```python
from pancake.ovenware.broker import get_broker

broker = get_broker()

# 订阅
async def handler(message):
    print(message)

await broker.subscribe("my.topic", handler)

# 发布
await broker.publish("my.topic", {"key": "value"})
```

## 配置

Redis 代理 URL 通过 YAML 或环境变量配置：

```yaml
redis:
  url: redis://localhost:6379
```
