"""LangGraph workflow for code analysis."""

import logging
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.nodes.business_logic_analysis import business_logic_analysis_node
from src.agents.nodes.business_logic_identification import (
    business_logic_identification_node,
)
from src.agents.nodes.data_model_analysis import data_model_analysis_node
from src.agents.nodes.data_model_identification import data_model_identification_node
from src.agents.nodes.product_requirements import product_requirements_node
from src.agents.nodes.repository_ingest import repository_ingest_node
from src.agents.nodes.routes_interfaces_analysis import routes_interfaces_analysis_node
from src.agents.nodes.routes_interfaces_identification import (
    routes_interfaces_identification_node,
)
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)


# Define a TypedDict for graph state to handle concurrent updates properly
class GraphState(TypedDict, total=False):
    """TypedDict for graph state with concurrent keys."""

    repository_url: str
    # Use Annotated with the last_value reducer for concurrent status updates
    status: Annotated[CodeAnalysisStatus, "last_value"]
    ingested_repository: Optional[str]
    technologies: Optional[list[str]]
    data_model_files: Optional[list[str]]
    data_model_analysis: Optional[str]
    routes_interfaces_files: Optional[list[str]]
    routes_interfaces_analysis: Optional[str]
    business_logic_files: Optional[list[str]]
    business_logic_analysis: Optional[str]
    product_requirements: Optional[str]
    architecture_documentation: Optional[str]
    analysis_id: Optional[str]
    # Use Annotated with the last_value reducer for concurrent error updates
    error: Annotated[Optional[str], "last_value"]


def create_code_analysis_graph() -> StateGraph:
    """
    Create the LangGraph workflow for code analysis.

    Returns:
        StateGraph: The LangGraph workflow without a checkpointer.
    """
    # Create the graph with proper TypedDict state
    graph = StateGraph(GraphState)

    # Add nodes to the graph
    graph.add_node("repository_ingest", repository_ingest_node)

    # Data model analysis branch
    graph.add_node("identify_data_models", data_model_identification_node)
    graph.add_node("analyze_data_models", data_model_analysis_node)

    # Routes and interfaces branch
    graph.add_node("identify_routes_interfaces", routes_interfaces_identification_node)
    graph.add_node("analyze_routes_interfaces", routes_interfaces_analysis_node)

    # Business logic branch
    graph.add_node("identify_business_logic", business_logic_identification_node)
    graph.add_node("analyze_business_logic", business_logic_analysis_node)

    # Product requirements node
    graph.add_node("generate_product_requirements", product_requirements_node)

    # Add edges from repository ingest to the identification nodes
    graph.add_edge(START, "repository_ingest")
    graph.add_edge("repository_ingest", "identify_data_models")
    graph.add_edge("repository_ingest", "identify_routes_interfaces")
    graph.add_edge("repository_ingest", "identify_business_logic")

    # Connect identification nodes to their respective analysis nodes
    graph.add_edge("identify_data_models", "analyze_data_models")
    graph.add_edge("identify_routes_interfaces", "analyze_routes_interfaces")
    graph.add_edge("identify_business_logic", "analyze_business_logic")

    # Connect all analysis nodes to the product requirements node
    graph.add_edge("analyze_data_models", "generate_product_requirements")
    graph.add_edge("analyze_routes_interfaces", "generate_product_requirements")
    graph.add_edge("analyze_business_logic", "generate_product_requirements")

    # Connect product requirements to the end
    graph.add_edge("generate_product_requirements", END)

    # Set the entry point
    graph.set_entry_point("repository_ingest")

    return graph


async def run_code_analysis_workflow(
    repository_url: str, analysis_id: str
) -> dict[str, Any]:
    """
    Run the code analysis workflow asynchronously.

    Args:
        repository_url: The URL of the repository to analyze.
        analysis_id: The ID of the code analysis document in MongoDB.

    Returns:
        dict[str, Any]: The final state of the workflow.
    """
    logger.info("Running code analysis workflow for repository: %s", repository_url)

    # Create the initial state as a dictionary for TypedDict compatibility
    initial_state = {
        "repository_url": repository_url,
        "analysis_id": analysis_id,
        "status": CodeAnalysisStatus.IN_PROGRESS,
    }

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

        # If there's an error in the final state, update the status
        if "error" in final_state and final_state["error"]:
            # Update status in the final state explicitly
            final_state["status"] = CodeAnalysisStatus.ERROR

            # Update the DB with error status
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR, error=final_state["error"]
            )
            await code_analysis_repository.update(analysis_id, update_data)
        else:
            # If there's no error and we have product_requirements, mark as completed
            if (
                "product_requirements" in final_state
                and final_state["product_requirements"]
            ):
                final_state["status"] = CodeAnalysisStatus.COMPLETED

                # Update the DB with completed status
                update_data = CodeAnalysisUpdate(status=CodeAnalysisStatus.COMPLETED)
                await code_analysis_repository.update(analysis_id, update_data)

        logger.info("Graph execution completed for analysis ID: %s", analysis_id)
        return final_state
    except Exception as e:
        logger.error("Error running code analysis workflow: %s", e)

        # Update the DB with error status
        update_data = CodeAnalysisUpdate(status=CodeAnalysisStatus.ERROR, error=str(e))
        await code_analysis_repository.update(analysis_id, update_data)

        raise
