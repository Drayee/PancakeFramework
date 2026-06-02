"""
Langgraph 插件 - 支持 IoC 和分布式开发
"""

from .core import langgraph_node, langgraph_edge, Main
from .ioc import IoCContainer, inject, container
from .remote import remote_node, HttpRemote, GrpcRemote
from .broker import event_node, SimpleBroker, RedisBroker
from .lifecycle import Lifecycle

__all__ = [
    # 核心（向后兼容）
    "langgraph_node", "langgraph_edge", "Main",
    # IoC
    "IoCContainer", "inject", "container",
    # 分布式
    "remote_node", "HttpRemote", "GrpcRemote",
    # 消息队列
    "event_node", "SimpleBroker", "RedisBroker",
    # 生命周期
    "Lifecycle",
]
