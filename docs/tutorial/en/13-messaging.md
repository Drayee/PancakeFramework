# 13. Message Queue

[← Previous](12-redis.md) | [Next →](14-langgraph.md)

---

## Overview

Pancake includes a built-in message queue module supporting event-driven architecture. It provides `@event_node` and `@on_event` decorators, with `SimpleBroker` (in-memory) and `RedisBroker` (distributed) implementations.

## @event_node — Event Node

```python
@event_node(name="process_order", event="order_created")
async def process_order(order_id: int):
    result = {"order_id": order_id, "status": "processed"}
    return result
# Auto-publishes "order_created" event after execution
```

## @on_event — Event Listener

```python
@on_event("order_created")
async def send_notification(message: dict):
    # message contains: source, result, data
    print(f"Order created: {message['result']}")
```

## SimpleBroker — In-Memory Queue

Default `SimpleBroker`, in-memory, for single-machine scenarios:

```python
broker = get_broker()
await broker.publish("user_registered", {"user_id": 1, "name": "Alice"})
await broker.subscribe("user_registered", lambda msg: print(msg))
```

## RedisBroker — Redis Queue

For distributed scenarios, use `RedisBroker`:

```python
from pancake.ovenware.broker import RedisBroker, set_broker

set_broker(RedisBroker(url="redis://localhost:6379"))
```

## Event-Driven Pattern

```python
# 1. Define event processing chain
@event_node(name="validate", event="validated")
async def validate_order(order: dict):
    if not order.get("items"):
        raise ValueError("Order has no items")
    return order

@on_event("validated")
async def process_payment(message: dict):
    order = message["result"]
    # Process payment...

@on_event("validated")
async def update_inventory(message: dict):
    order = message["result"]
    # Update inventory...
```

---

[← Previous](12-redis.md) | [Next →](14-langgraph.md)
