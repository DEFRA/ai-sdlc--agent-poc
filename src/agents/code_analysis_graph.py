"""LangGraph workflow for code analysis."""

import logging
from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from src.agents.nodes.data_model_analysis import data_model_analysis_node
from src.agents.nodes.data_model_identification import data_model_identification_node
from src.agents.nodes.repository_ingest import repository_ingest_node
from src.agents.nodes.routes_interfaces_analysis import routes_interfaces_analysis_node
from src.agents.nodes.routes_interfaces_identification import (
    routes_interfaces_identification_node,
)
from src.agents.states.code_analysis_state import CodeAnalysisState

logger = logging.getLogger(__name__)


def create_code_analysis_graph() -> StateGraph:
    """
    Create the LangGraph workflow for code analysis with parallel branches.

    Returns:
        StateGraph: The compiled workflow graph.
    """
    # Create main graph
    graph = StateGraph(CodeAnalysisState)

    # Add nodes to the graph
    graph.add_node("repository_ingest", repository_ingest_node)

    # Add identification nodes
    graph.add_node("identify_data_models", data_model_identification_node)
    graph.add_node("identify_routes_interfaces", routes_interfaces_identification_node)

    # Add analysis nodes
    graph.add_node("analyze_data_models", data_model_analysis_node)
    graph.add_node("analyze_routes_interfaces", routes_interfaces_analysis_node)

    # Add join node that doesn't modify state - just passes it through
    graph.add_node("join", lambda state: state)

    # Add edges - start with repository ingest
    graph.add_edge(START, "repository_ingest")

    # Fan out from repository_ingest to both identification nodes
    graph.add_edge("repository_ingest", "identify_data_models")
    graph.add_edge("repository_ingest", "identify_routes_interfaces")

    # Connect identification nodes to their respective analysis nodes
    graph.add_edge("identify_data_models", "analyze_data_models")
    graph.add_edge("identify_routes_interfaces", "analyze_routes_interfaces")

    # Fan in - connect both analysis nodes to the join node
    graph.add_edge("analyze_data_models", "join")
    graph.add_edge("analyze_routes_interfaces", "join")

    # Connect join node to END
    graph.add_edge("join", END)

    # Set entry point
    graph.set_entry_point("repository_ingest")

    return graph


async def run_code_analysis_workflow(
    repository_url: str, analysis_id: str
) -> CodeAnalysisState:
    """
    Run the code analysis workflow asynchronously.

    Args:
        repository_url: The URL of the repository to analyze.
        analysis_id: The ID of the code analysis document in MongoDB.

    Returns:
        CodeAnalysisState: The final state of the workflow.
    """
    logger.info("Running code analysis workflow for repository: %s", repository_url)

    # Create the initial state
    initial_state = CodeAnalysisState(
        repository_url=repository_url, analysis_id=analysis_id
    )

    # Create the base graph
    base_graph = create_code_analysis_graph()

    # Define the config for the graph
    # Using a dict without type annotations - will be handled by the graph internally
    config: dict[str, Any] = {"configurable": {"thread_id": analysis_id}}

    # Run the graph asynchronously
    try:
        logger.info("Creating code analysis graph for analysis ID: %s", analysis_id)

        # Compile the graph
        graph = base_graph.compile()

        logger.info("Starting graph execution for analysis ID: %s", analysis_id)
        # Execute the graph with the config
        # Cast the config to Any to bypass the type checking issue
        final_state = await graph.ainvoke(initial_state, config=cast(Any, config))
        final_state_cast = cast(CodeAnalysisState, final_state)

        logger.info("Graph execution completed for analysis ID: %s", analysis_id)
        return final_state_cast
    except Exception as e:
        logger.error("Error running code analysis workflow: %s", e)
        raise
