## Private State Example

let's cover the case of passing [private state](https://langchain-ai.github.io/langgraph/how-tos/pass_private_state/) between nodes.

This is useful for anything needed as part of the intermediate working logic of the graph, but not relevant for the overall graph input or output.

We'll define an `OverallState` and a `PrivateState`.

`node_2` uses `PrivateState` as input, but writes out to `OverallState`.

```python
from typing_extensions import TypedDict

from IPython.display import Image, display

from langgraph.graph import StateGraph, START, END



class OverallState(TypedDict):

foo: int



class PrivateState(TypedDict):

baz: int



def node_1(state: OverallState) -> PrivateState:

print("---Node 1---")

return {"baz": state['foo'] + 1}



def node_2(state: PrivateState) -> OverallState:

print("---Node 2---")

return {"foo": state['baz'] + 1}



# Build graph

builder = StateGraph(OverallState)

builder.add_node("node_1", node_1)

builder.add_node("node_2", node_2)



# Logic

builder.add_edge(START, "node_1")

builder.add_edge("node_1", "node_2")

builder.add_edge("node_2", END)



# Add

graph = builder.compile()



# View

display(Image(graph.get_graph().draw_mermaid_png()))
```

If this is executed, the output is `{'foo': 3}`

`baz` is only included in `PrivateState`.


`node_2` uses `PrivateState` as input, but writes out to `OverallState`.


So, we can see that `baz` is excluded from the graph output because it is not in `OverallState`.
