"""Routes and Interfaces Analysis Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.analysis_node_factory import create_analysis_node
from src.agents.states.analysis_state import AnalysisState
from src.agents.states.code_analysis_state import CodeAnalysisState

logger = logging.getLogger(__name__)

# System message for the routes and interfaces analysis agent
ROUTES_INTERFACES_ANALYSIS_SYSTEM_MESSAGE = """
You are an API architect and UI/UX expert tasked with analyzing routes, APIs, and interfaces in a codebase.

You have been provided with a list of routes and interfaces related files that you need to analyze.
You should use the retrieve_files tool to get the content of these files.
"""

# Template for routes and interfaces analysis prompt
ROUTES_INTERFACES_ANALYSIS_PROMPT = """
Analyze the routes, APIs, and interfaces in the following files from repository {repository_url}:

Files: {file_list}

---

Once you have the file contents, generate a comprehensive routes and interfaces analysis document that includes:

1. Overview of API and Interface Architecture
   - High-level description of the API/interface design
   - Major endpoints and their purposes
   - Client-server interaction patterns

2. API Endpoints Analysis
   - Detailed breakdown of all API endpoints
   - HTTP methods, URL patterns, and parameters
   - Request/response formats and data structures
   - Authentication and authorization mechanisms

3. API Visualization
   - Create a visual representation of the API structure using mermaid.js
   - Group endpoints logically by resource or functionality

4. User Interface Structure
   - Component hierarchy and page structure
   - Navigation flow and routing patterns
   - State management approach

5. Integration Points
   - How frontend and backend components interact
   - API consumption patterns
   - Data transformation between client and server

Format the output in markdown, with the API visualization in a mermaid code block.

The API visualization is only needed if there are actual API endpoints defined in the codebase.
"""

# Create the factory node
_factory_node = create_analysis_node(
    analysis_type="Routes and Interfaces",
    input_field_name="routes_interfaces_files",
    output_field_name="routes_interfaces_analysis",
    system_message=ROUTES_INTERFACES_ANALYSIS_SYSTEM_MESSAGE,
    prompt_template=ROUTES_INTERFACES_ANALYSIS_PROMPT,
)


# Create a wrapper node that translates between CodeAnalysisState and AnalysisState
async def routes_interfaces_analysis_node(
    state: CodeAnalysisState,
) -> CodeAnalysisState:
    """
    Wrapper node for routes and interfaces analysis.

    This node:
    1. Converts from CodeAnalysisState to AnalysisState
    2. Calls the factory node with config
    3. Updates CodeAnalysisState with results

    Args:
        state: The current CodeAnalysisState

    Returns:
        Updated CodeAnalysisState
    """
    try:
        # Check if we have the required input in current state
        if not state.routes_interfaces_files and state.analysis_id:
            # If not in state but we have analysis_id, try to fetch from MongoDB
            logger.info(
                "routes_interfaces_files not found in state, trying to fetch from MongoDB"
            )
            from src.repositories.code_analysis import code_analysis_repository

            # Retrieve the document from MongoDB
            analysis_doc = await code_analysis_repository.get(state.analysis_id)
            if analysis_doc and analysis_doc.routes_interfaces_files:
                logger.info(
                    "Successfully retrieved routes_interfaces_files from MongoDB: %d files",
                    len(analysis_doc.routes_interfaces_files),
                )
                state.routes_interfaces_files = analysis_doc.routes_interfaces_files
            else:
                logger.error("Could not retrieve routes_interfaces_files from MongoDB")
                state.error = "No routes and interfaces files available for analysis - not found in state or MongoDB"
                return state
        elif not state.routes_interfaces_files:
            state.error = "No routes and interfaces files available for analysis"
            logger.error(
                "No routes_interfaces_files found in state and no analysis_id to fetch from MongoDB"
            )
            return state

        # Log the files that will be analyzed
        logger.info(
            "Starting Routes and Interfaces Analysis for %d files: %s",
            len(state.routes_interfaces_files),
            state.routes_interfaces_files[:3],  # Log first 3 files for brevity
        )

        # Create analysis state with routes_interfaces_files from main state and empty data_model_files
        # Since data_model_files is required but we don't need it for this node
        analysis_state = AnalysisState(
            data_model_files=[], routes_interfaces_files=state.routes_interfaces_files
        )

        # Create config with read-only values
        config = {
            "configurable": {
                "analysis_id": state.analysis_id,
                "repository_url": state.repository_url,
            }
        }

        # Run the factory node
        result_state = await _factory_node(analysis_state, config)

        # Update the main state with results
        if result_state.routes_interfaces_analysis:
            state.routes_interfaces_analysis = result_state.routes_interfaces_analysis
            logger.info(
                "Routes and Interfaces Analysis completed successfully. Analysis length: %d characters",
                len(state.routes_interfaces_analysis),
            )

        if result_state.error:
            state.error = result_state.error
            logger.error("Error from factory node: %s", state.error)

        return state
    except Exception as e:
        error_msg = f"Error in Routes and Interfaces Analysis Node: {str(e)}"
        logger.error(error_msg)
        state.error = error_msg

        # Update MongoDB if we have an analysis_id
        if state.analysis_id:
            from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
            from src.repositories.code_analysis import code_analysis_repository

            try:
                update_data = CodeAnalysisUpdate(
                    status=CodeAnalysisStatus.ERROR, error=error_msg
                )
                await code_analysis_repository.update(state.analysis_id, update_data)
            except Exception as update_error:
                logger.error(
                    "Error updating analysis status after node failure: %s",
                    update_error,
                )

        return state
