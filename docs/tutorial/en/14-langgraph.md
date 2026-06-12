# 14. LangGraph Plugin — Workflow

[← Previous](13-messaging.md) | [Next →](15-remote.md)

---

## Overview

`pancake-langgraph` provides LangGraph state graph workflow integration with nodes, edges, and conditional branching.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>langgraph</artifactId>
</dependency>
```

## Configuration

```yaml
langgraph:
  enable_graph: true
  state_fields:
    messages: list
    context: dict
```

## Defining Nodes

```python
@langgraph_node(name="analyze")
async def analyze_node(state):
    messages = state.get("messages", [])
    # Processing logic
    return {"messages": messages + ["Analysis complete"]}

@langgraph_node(name="decide")
async def decide_node(state):
    return {"next": "action_a"}
```

## Defining Edges

```python
@langgraph_edge(from_node="analyze", to_node="decide")
def analyze_to_decide(state):
    return True

@langgraph_edge(from_node="decide", to_node="action_a", condition=lambda s: s.get("next") == "action_a")
def decide_to_action_a(state):
    return True
```

---

[← Previous](13-messaging.md) | [Next →](15-remote.md)
