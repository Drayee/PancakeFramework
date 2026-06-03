# Lifecycle Management

Manage component lifecycle with hooks: init, start, stop, error, complete.

## Lifecycle Base Class

```python
class MyService(Lifecycle):
    async def on_init(self):
        """Called once when created"""
        self.cache = {}
        await self.load_config()

    async def on_start(self):
        """Called before processing begins"""
        await self.connect_db()

    async def on_stop(self):
        """Called when shutting down"""
        await self.close_connections()

    async def on_error(self, error: Exception):
        """Called when an error occurs"""
        logger.error(f"Error: {error}")

    async def on_complete(self, result=None):
        """Called after processing completes"""
        logger.info(f"Done: {result}")

    async def process(self, state=None):
        """Main processing method (required)"""
        return {"status": "ok"}
```

## @lifecycle_node Decorator

Automatically manages lifecycle for langgraph nodes:

```python
@lifecycle_node("worker")
class WorkerNode(Lifecycle):
    async def on_init(self):
        self.db = await connect_db()

    async def process(self, state):
        return await self.db.query(...)
```

The decorator:
1. Creates a single instance (reused across calls)
2. Calls `on_init()` and `on_start()` on first invocation
3. Calls `process()` for each request
4. Calls `on_complete()` after processing

## LifecycleManager

Manages multiple lifecycle instances programmatically.

```python
manager = LifecycleManager()

# Register instances
await manager.register("worker", WorkerNode())

# Initialize all
await manager.initialize()

# Start all
await manager.start()

# Stop specific
await manager.stop("worker")

# Shutdown everything
await manager.shutdown_all()
```

## Context Manager

```python
async with lifecycle_context():
    # All lifecycle instances are managed
    # Automatically shuts down on exit
    ...
```

## Lifecycle States

```
Created → Initialized → Started → (Processing) → Stopped
                                        ↓
                                     on_error
```
