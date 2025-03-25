import asyncio
from typing import Any, Union

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


# Step 1: Define the Parent Graph's State
class ParentState(BaseModel):
    shared_data: str = Field(description="Data to be shared across subgraphs")
    subgraph_results: list[str] = Field(
        default_factory=list, description="Results from subgraphs"
    )

    def combine_results(self, other: "ParentState") -> "ParentState":
        """Combine results from two states."""
        return ParentState(
            shared_data=self.shared_data,
            subgraph_results=self.subgraph_results + other.subgraph_results,
        )


# Step 2: Define the Subgraph's State Type
class SubgraphState(BaseModel):
    input_data: str = Field(description="Input data to be processed by the subgraph")
    result: str = Field(default="", description="Result of the subgraph processing")

    def model_dump(self) -> dict[str, str]:
        """Convert the model to a dictionary."""
        return {"input_data": self.input_data, "result": self.result}


# Step 3: Implement the Subgraph
async def subgraph_node(state: Union[dict[str, str], SubgraphState]) -> dict[str, str]:
    # Convert to SubgraphState if needed
    state_model = state if isinstance(state, SubgraphState) else SubgraphState(**state)
    # Process the input
    result = state_model.input_data.upper()
    # Return as dict
    return {"result": result}


subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node("process", subgraph_node)
subgraph_builder.set_entry_point("process")
subgraph_builder.set_finish_point("process")
subgraph = subgraph_builder.compile()

# Print Subgraph Mermaid diagram
print("\nSubgraph visualization in Mermaid:")
print(subgraph.get_graph().draw_mermaid())


# Step 4: Integrate the Subgraph into the Parent Graph
async def invoke_subgraph(state: Union[dict[str, Any], ParentState]) -> dict[str, Any]:
    # Convert to ParentState if needed
    state_model = ParentState(**state) if isinstance(state, dict) else state
    # Transform parent state to subgraph state
    subgraph_input = {"input_data": state_model.shared_data}
    # Invoke the subgraph
    subgraph_output = await subgraph.ainvoke(subgraph_input)
    # Transform subgraph output back to parent state
    return {"subgraph_results": [subgraph_output["result"]]}


# Step 5: Implement Asynchronous Parallel Execution
async def parallel_invocation(
    state: Union[dict[str, Any], ParentState],
) -> dict[str, Any]:
    # Convert to ParentState if needed
    state_model = ParentState(**state) if isinstance(state, dict) else state

    # Create async tasks for parallel execution
    task1 = asyncio.create_task(
        invoke_subgraph(
            {"shared_data": state_model.shared_data + " task1", "subgraph_results": []}
        )
    )
    task2 = asyncio.create_task(
        invoke_subgraph(
            {"shared_data": state_model.shared_data + " task2", "subgraph_results": []}
        )
    )

    # Execute tasks concurrently and wait for both to complete
    results = await asyncio.gather(task1, task2)

    # Combine results
    all_results = []
    for result in results:
        all_results.extend(result["subgraph_results"])

    return {"shared_data": state_model.shared_data, "subgraph_results": all_results}


# Step 6: Merge Subgraph States into the Parent State
async def merge_results(state: Union[dict[str, Any], ParentState]) -> dict[str, Any]:
    # Convert to ParentState if needed
    state_model = ParentState(**state) if isinstance(state, dict) else state
    # Combine results from subgraphs
    combined_result = " | ".join(state_model.subgraph_results)
    return {"shared_data": combined_result}


# Build the Parent Graph
parent_builder = StateGraph(ParentState)
parent_builder.add_node(
    "start", lambda _: {"shared_data": "initial data", "subgraph_results": []}
)
parent_builder.set_entry_point("start")
parent_builder.add_node("parallel_execution", parallel_invocation)
parent_builder.add_node("merge_results", merge_results)
parent_builder.add_edge(START, "start")
parent_builder.add_edge("start", "parallel_execution")
parent_builder.add_edge("parallel_execution", "merge_results")
parent_builder.add_edge("merge_results", END)
parent_graph = parent_builder.compile()

# Print Parent Graph Mermaid diagram
print("\nParent Graph visualization in Mermaid:")
print(parent_graph.get_graph().draw_mermaid())


# Execute the Parent Graph
async def main():
    initial_state = {"shared_data": "initial data", "subgraph_results": []}
    async for step in parent_graph.astream(initial_state):
        print(step)


if __name__ == "__main__":
    asyncio.run(main())
