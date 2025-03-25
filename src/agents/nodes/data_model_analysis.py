"""Data Model Analysis Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.analysis_node_factory import create_analysis_node
from src.agents.states.analysis_state import AnalysisState
from src.agents.states.code_analysis_state import CodeAnalysisState

logger = logging.getLogger(__name__)

# System message for the data model analysis agent
DATA_MODEL_ANALYSIS_SYSTEM_MESSAGE = """
You are an data architect tasked with analyzing data models in a codebase.

You have been provided with a list of data model related files that you need to analyze.
You should use the retrieve_files tool to get the content of these files.
"""

# Template for data model analysis prompt
DATA_MODEL_ANALYSIS_PROMPT = """
Analyze the data models in the following files from repository {repository_url}:

Files: {file_list}

---

Once you have the file contents, generate a comprehensive data model analysis document that includes:

1. Overview of the Data Architecture
   - High-level description of the data model
   - Key entities and their purposes
   - Data persistence approach

2. Logical Data Model
   - Detailed description of each entity
   - Attributes and their types
   - Relationships between entities

3. Entity Relationship Diagram
   - Create a mermaid.js ERD diagram showing all entities and their relationships
   - Use proper mermaid.js ERD syntax
   - Include cardinality in relationships

4. Implementation Details
   - How the data model is implemented
   - Any ORM or database specific details
   - Data validation and constraints

5. API Integration
   - How the data model is exposed via APIs
   - Data transfer objects (DTOs)
   - Serialization/deserialization approaches

Format the output in markdown, with the ERD diagram in a mermaid code block.

The output must have a ERD diagram, unless there are no entities or relationships in the data model.
"""

# Create the factory node
_factory_node = create_analysis_node(
    analysis_type="Data Model",
    input_field_name="data_model_files",
    output_field_name="data_model_analysis",
    system_message=DATA_MODEL_ANALYSIS_SYSTEM_MESSAGE,
    prompt_template=DATA_MODEL_ANALYSIS_PROMPT,
)


# Create a wrapper node that translates between CodeAnalysisState and AnalysisState
async def data_model_analysis_node(state: CodeAnalysisState) -> CodeAnalysisState:
    """
    Wrapper node for data model analysis.

    This node:
    1. Converts from CodeAnalysisState to AnalysisState
    2. Calls the factory node with config
    3. Updates CodeAnalysisState with results

    Args:
        state: The current CodeAnalysisState

    Returns:
        Updated CodeAnalysisState
    """
    # Check if we have the required input
    if not state.data_model_files:
        state.error = "No data model files available for analysis"
        return state

    # Create analysis state with data_model_files from main state
    analysis_state = AnalysisState(data_model_files=state.data_model_files)

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
    if result_state.data_model_analysis:
        state.data_model_analysis = result_state.data_model_analysis

    if result_state.error:
        state.error = result_state.error

    return state
