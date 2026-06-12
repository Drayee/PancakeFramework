# 14. LangGraph 插件 — 工作流

[← 上一节](13-messaging.md) | [下一节 →](15-remote.md)

---

## 概述

`pancake-langgraph` 提供 LangGraph 状态图工作流集成，支持节点、边、条件分支。

## 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>langgraph</artifactId>
</dependency>
```

## 配置

```yaml
langgraph:
  enable_graph: true
  state_fields:
    messages: list
    context: dict
```

## 定义节点

```python
@langgraph_node(name="analyze")
async def analyze_node(state):
    messages = state.get("messages", [])
    # 处理逻辑
    return {"messages": messages + ["分析完成"]}

@langgraph_node(name="decide")
async def decide_node(state):
    return {"next": "action_a"}
```

## 定义边

```python
@langgraph_edge(from_node="analyze", to_node="decide")
def analyze_to_decide(state):
    return True

@langgraph_edge(from_node="decide", to_node="action_a", condition=lambda s: s.get("next") == "action_a")
def decide_to_action_a(state):
    return True
```

---

[← 上一节](13-messaging.md) | [下一节 →](15-remote.md)
