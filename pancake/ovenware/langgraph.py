"""
Langgraph 插件 - 支持 IoC 和分布式开发
重构为子模块结构，保留原有功能
"""

import logging

logger = logging.getLogger(__name__)

# 向后兼容导入
from .langgraph.core import langgraph_node, langgraph_edge, Main
from .ioc import IoCContainer, inject, container
from .langgraph.remote import remote_node, HttpRemote, GrpcRemote, proxy
from .langgraph.broker import event_node, on_event, SimpleBroker, RedisBroker, get_broker, set_broker
from .langgraph.lifecycle import Lifecycle, LifecycleManager, lifecycle_node, lifecycle_context, lifecycle_manager

# 导出所有功能
__all__ = [
    # 核心（向后兼容）
    "langgraph_node", "langgraph_edge", "Main",
    # IoC
    "IoCContainer", "inject", "container",
    # 分布式
    "remote_node", "HttpRemote", "GrpcRemote", "proxy",
    # 消息队列
    "event_node", "on_event", "SimpleBroker", "RedisBroker", "get_broker", "set_broker",
    # 生命周期
    "Lifecycle", "LifecycleManager", "lifecycle_node", "lifecycle_context", "lifecycle_manager",
]
