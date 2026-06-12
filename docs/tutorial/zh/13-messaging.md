# 13. 消息队列

[← 上一节](12-redis.md) | [下一节 →](14-langgraph.md)

---

## 概述

Pancake 内置消息队列模块，支持事件驱动架构。提供 `@event_node` 和 `@on_event` 装饰器，以及 `SimpleBroker`（内存）和 `RedisBroker`（分布式）两种实现。

## @event_node — 事件节点

```python
@event_node(name="process_order", event="order_created")
async def process_order(order_id: int):
    # 处理订单
    result = {"order_id": order_id, "status": "processed"}
    return result
# 执行后自动发布 "order_created" 事件
```

## @on_event — 事件监听

```python
@on_event("order_created")
async def send_notification(message: dict):
    # message 包含: source, result, data
    print(f"订单已创建: {message['result']}")
```

## SimpleBroker — 内存消息队列

默认使用 `SimpleBroker`，基于内存，适用于单机场景：

```python
broker = get_broker()
await broker.publish("user_registered", {"user_id": 1, "name": "Alice"})
await broker.subscribe("user_registered", lambda msg: print(msg))
```

## RedisBroker — Redis 消息队列

分布式场景使用 `RedisBroker`：

```python
from pancake.ovenware.broker import RedisBroker, set_broker

set_broker(RedisBroker(url="redis://localhost:6379"))
```

## 事件驱动模式

```python
# 1. 定义事件处理链
@event_node(name="validate", event="validated")
async def validate_order(order: dict):
    if not order.get("items"):
        raise ValueError("订单无商品")
    return order

@on_event("validated")
async def process_payment(message: dict):
    order = message["result"]
    # 处理支付...

@on_event("validated")
async def update_inventory(message: dict):
    order = message["result"]
    # 更新库存...
```

---

[← 上一节](12-redis.md) | [下一节 →](14-langgraph.md)
