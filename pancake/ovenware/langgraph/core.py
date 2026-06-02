"""
Langgraph 核心引擎
保留原有 langgraph_node/edge 功能，扩展 IoC 和分布式支持
"""

import functools
import inspect
import logging
from pancake import oven

from ..inject import _get_param_types

logger = logging.getLogger(__name__)


class Main(InitAction):
    """Langgraph 主类 - 构建并编译状态图"""

    def __init__(self):
        self.app = None
        self.workflow = None
        oven.pancake_dough["langgraph_node"] = {}
        oven.pancake_dough["langgraph_edge"] = {}
        oven.pancake_other["first_node"] = []
        oven.pancake_other["last_node"] = []
        oven.pancake_other["langgraph_map"] = {}

    def build(self):
        # 延迟导入外部 langgraph 包（可选依赖）
        try:
            from langgraph.graph import StateGraph, END
            from typing import TypedDict, Annotated, Sequence
            from langchain_core.messages import BaseMessage
            from langgraph.graph.message import add_messages

            class State(TypedDict):
                messages: Annotated[Sequence[BaseMessage], add_messages]

            self.workflow = StateGraph(State)

            # 注册节点
            for name, func in oven.pancake_dough["langgraph_node"].items():
                self.workflow.add_node(name, func)

            # 设置入口节点
            can_run = False
            for first_node in oven.pancake_other["first_node"]:
                self.workflow.set_entry_point(first_node)
                can_run = True

            # 设置出口节点
            for last_node in oven.pancake_other["last_node"]:
                self.workflow.add_edge(last_node, END)

            # 注册边
            for name, func in oven.pancake_dough["langgraph_edge"].items():
                from_node, map = oven.pancake_other["langgraph_edge"][name]
                if map is None:
                    self.workflow.add_edge(from_node, func)
                else:
                    self.workflow.add_conditional_edges(from_node, func, map)

            # 编译图
            if can_run:
                self.app = self.workflow.compile()

        except ImportError:
            logger.info("langgraph 包未安装，跳过图编译（本地节点仍可用）")

        # 保存到 oven
        oven.pancake_other["langgraph_app"] = self.app
        oven.pancake_other["get_graph"] = self._get_graph

        logger.info("Langgraph 构建完成")

    def _get_graph(self):
        """获取图的可视化"""
        try:
            from IPython.display import display, Image
            display(Image(self.app.get_graph(xray=True).draw_png()))
        except Exception as e:
            logger.error(f"获取 langgraph 图失败: {e}")

    def loop_method(self):
        """运行图（如果需要）"""
        if self.app:
            logger.info("Langgraph 图已就绪，可通过 langgraph_app 调用")


def langgraph_node(name: str = None, first_last: bool = None):
    """
    注册 langgraph 节点

    Args:
        name: 节点名称
        first_last: True=入口节点, False=出口节点, None=中间节点
    """
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__

        # 注册节点
        oven.pancake_dough["langgraph_node"][name] = func

        # 设置入口/出口
        if first_last is not None:
            if first_last:
                oven.pancake_other["first_node"].append(name)
            else:
                oven.pancake_other["last_node"].append(name)

        # 获取参数类型
        param_types = _get_param_types(func).keys()

        @functools.wraps(func)
        def wrapper(state, config, writer, store, stream):
            kwargs = {}
            for param_item_ in param_types:
                if param_item_ in ["state", "config", "writer", "store", "stream"]:
                    kwargs[param_item_] = locals()[param_item_]
                else:
                    try:
                        kwargs[param_item_] = oven.pancake_other["langgraph_map"][param_item_]
                    except (KeyError, TypeError):
                        kwargs[param_item_] = None

            return_information = func(**kwargs)

            # 存储返回值到共享 map
            if return_information is not None:
                if type(return_information) is dict:
                    oven.pancake_other["langgraph_map"].update(return_information)
                else:
                    oven.pancake_other["langgraph_map"][name] = return_information

        return wrapper
    return decorator


def langgraph_edge(from_node: str = None, map: dict = None, name: str = None):
    """
    注册 langgraph 边

    Args:
        from_node: 源节点
        map: 条件边映射 {条件值: 目标节点}
        name: 边名称
    """
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__

        # 注册边
        oven.pancake_dough["langgraph_edge"][name] = func
        oven.pancake_other["langgraph_edge"][name] = [from_node, map]

        # 获取参数类型
        param_types = _get_param_types(func).keys()

        @functools.wraps(func)
        def wrapper(state):
            kwargs = {}
            for param_item_ in param_types:
                if param_item_ == "state":
                    kwargs[param_item_] = state
                else:
                    try:
                        kwargs[param_item_] = oven.pancake_other["langgraph_map"][param_item_]
                    except (KeyError, TypeError):
                        kwargs[param_item_] = None
            return func(**kwargs)

        return wrapper
    return decorator
