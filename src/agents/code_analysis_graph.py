"""LangGraph workflow for code analysis."""

import logging

from langgraph.graph import END, START, StateGraph

from src.agents.nodes.data_model_analysis import data_model_analysis_node
from src.agents.nodes.data_model_identification import data_model_identification_node
from src.agents.nodes.repository_ingest import repository_ingest_node
from src.agents.states.code_analysis_state import CodeAnalysisState

logger = logging.getLogger(__name__)


def create_code_analysis_graph() -> StateGraph:
    """
    Create the LangGraph workflow for code analysis.

    Returns:
        StateGraph: The LangGraph workflow without a checkpointer.
    """
    # Create the graph with the code analysis state
    graph = StateGraph(CodeAnalysisState)

    # Add nodes to the graph
    graph.add_node("repository_ingest", repository_ingest_node)
    graph.add_node("identify_data_models", data_model_identification_node)
    graph.add_node("analyze_data_models", data_model_analysis_node)
    # omitting while testing other steps in the graph
    # graph.add_node("generate_architecture_doc", architecture_documentation_node)

    # Add edges between nodes
    graph.add_edge(START, "repository_ingest")
    graph.add_edge("repository_ingest", "identify_data_models")
    graph.add_edge("identify_data_models", "analyze_data_models")
    # omitting while testing other steps in the graph
    # graph.add_edge("analyze_data_models", "generate_architecture_doc")
    graph.add_edge("analyze_data_models", END)

    # Set the entry point
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

    # Define the config for the checkpointer
    config = {"configurable": {"thread_id": analysis_id}}

    # Run the graph asynchronously with MongoDB checkpointer
    try:
        logger.info("Creating code analysis graph for analysis ID: %s", analysis_id)

        # Compile the graph without a checkpointer for now
        # This allows us to run the workflow without persistence temporarily
        graph = base_graph.compile()

        logger.info("Starting graph execution for analysis ID: %s", analysis_id)
        # Execute the graph with the config
        final_state = await graph.ainvoke(initial_state, config=config)

        logger.info("Graph execution completed for analysis ID: %s", analysis_id)
        return final_state
    except Exception as e:
        logger.error("Error running code analysis workflow: %s", e)
        raise
