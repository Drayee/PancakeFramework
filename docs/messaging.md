# Message Queue

Event-driven messaging with in-memory and Redis brokers.

## @event_node

Publish events when a function completes:

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}
```

The result is automatically published to the specified event topic.

## @on_event

Subscribe to events:

```python
@on_event("order.created")
async def notify_inventory(message):
    print(f"Order received: {message}")

@on_event("order.created")
async def send_confirmation(message):
    await email.send(message["data"])
```

## Brokers

### SimpleBroker (default)

In-memory message queue. No external dependencies.

- Messages are delivered synchronously within the same process
- Handlers registered with `@on_event` are auto-subscribed on first publish

### RedisBroker

Redis Pub/Sub based. Requires Redis.

```python
from pancake.ovenware.broker import RedisBroker, set_broker

set_broker(RedisBroker(url="redis://localhost:6379"))
```

Features:
- Cross-process messaging
- Exponential backoff retry on connection errors
- Auto-reconnect

## Programmatic Usage

```python
from pancake.ovenware.broker import get_broker

broker = get_broker()

# Subscribe
async def handler(message):
    print(message)

await broker.subscribe("my.topic", handler)

# Publish
await broker.publish("my.topic", {"key": "value"})
```

## Configuration

Redis broker URL is configured via YAML or environment:

```yaml
redis:
  url: redis://localhost:6379
```
