"""
Langgraph 插件 - AI 工作流核心
消息队列、生命周期、远程调用已移至 ovenware 顶层
"""

from .core import langgraph_node, langgraph_edge, Main

# 可选插件：未启用时不影响 langgraph 核心功能
try:
    from ..broker import event_node, on_event, SimpleBroker, RedisBroker, get_broker, set_broker
except ImportError:
    pass

try:
    from ..lifecycle import Lifecycle, LifecycleManager, lifecycle_node, lifecycle_context, lifecycle_manager
except ImportError:
    pass

try:
    from ..remote import remote_node, HttpRemote, GrpcRemote, proxy
except ImportError:
    pass
