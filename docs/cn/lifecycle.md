# 生命周期管理

通过钩子管理组件生命周期：初始化、启动、停止、错误处理、完成。

## Lifecycle 基类

```python
class MyService(Lifecycle):
    async def on_init(self):
        """创建时调用"""
        self.cache = {}
        await self.load_config()

    async def on_start(self):
        """开始处理前调用"""
        await self.connect_db()

    async def on_stop(self):
        """停止时调用"""
        await self.close_connections()

    async def on_error(self, error: Exception):
        """发生错误时调用"""
        logger.error(f"错误: {error}")

    async def on_complete(self, result=None):
        """处理完成后调用"""
        logger.info(f"完成: {result}")

    async def process(self, state=None):
        """主处理方法（必须实现）"""
        return {"status": "ok"}
```

## @lifecycle_node 装饰器

自动管理 langgraph 节点的生命周期：

```python
@lifecycle_node("worker")
class WorkerNode(Lifecycle):
    async def on_init(self):
        self.db = await connect_db()

    async def process(self, state):
        return await self.db.query(...)
```

装饰器行为：
1. 创建单个实例（跨调用复用）
2. 首次调用时执行 `on_init()` 和 `on_start()`
3. 每次请求执行 `process()`
4. 处理完成后执行 `on_complete()`

## LifecycleManager

编程方式管理多个生命周期实例。

```python
manager = LifecycleManager()

# 注册实例
await manager.register("worker", WorkerNode())

# 初始化全部
await manager.initialize()

# 启动全部
await manager.start()

# 停止指定实例
await manager.stop("worker")

# 关闭所有
await manager.shutdown_all()
```

## 上下文管理器

```python
async with lifecycle_context():
    # 所有生命周期实例被管理
    # 退出时自动关闭
    ...
```

## 生命周期状态

```
已创建 → 已初始化 → 已启动 → (处理中) → 已停止
                                  ↓
                               on_error
```
