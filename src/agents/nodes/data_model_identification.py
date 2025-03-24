"""Data Model Identification Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.identification_node_factory import (
    create_identification_node,
)
from src.agents.states.code_analysis_state import CodeAnalysisState
from src.agents.states.identification_state import IdentificationState

logger = logging.getLogger(__name__)

# Template for identifying data model files
DATA_MODEL_IDENTIFICATION_TEMPLATE = """
You are an expert software architect tasked with identifying all files in a codebase that are related to data models.

You have been provided with information about the repository in the <repository_information> tag.

<repository_information>
{ingested_repository}
</repository_information>

Analyze the repository content and identify all files that:
1. Define data models or schemas
2. Handle data persistence (database operations, ORM mappings)
3. Expose data models via external interfaces (API endpoints, GraphQL schemas)

Return a list of file paths. Each path should be a valid file path from the repository.
"""


# Create the factory node
_factory_node = create_identification_node(
    prompt_template=DATA_MODEL_IDENTIFICATION_TEMPLATE,
    state_field_name="data_model_files",
)


# Create a wrapper node that translates between CodeAnalysisState and IdentificationState
async def data_model_identification_node(state: CodeAnalysisState) -> CodeAnalysisState:
    """
    Wrapper node for data model identification.

    This node:
    1. Converts from CodeAnalysisState to IdentificationState
    2. Calls the factory node with config
    3. Updates CodeAnalysisState with results

    Args:
        state: The current CodeAnalysisState

    Returns:
        Updated CodeAnalysisState
    """
    # Create identification state (empty as we're using config)
    id_state = IdentificationState()

    # Create config with read-only values
    config = {
        "configurable": {
            "analysis_id": state.analysis_id,
            "repository_url": state.repository_url,
            "ingested_repository": state.ingested_repository,
        }
    }

    # Run the factory node
    result_state = await _factory_node(id_state, config)

    # Update the main state with results
    if result_state.data_model_files:
        state.data_model_files = result_state.data_model_files

    if result_state.error:
        state.error = result_state.error

    return state
