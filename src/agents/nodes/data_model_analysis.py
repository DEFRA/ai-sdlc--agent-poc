"""Data Model Analysis Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.analysis_node_factory import create_analysis_node

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

# Create the data model analysis node using the factory
data_model_analysis_node = create_analysis_node(
    analysis_type="Data Model",
    input_field_name="data_model_files",
    output_field_name="data_model_analysis",
    system_message=DATA_MODEL_ANALYSIS_SYSTEM_MESSAGE,
    prompt_template=DATA_MODEL_ANALYSIS_PROMPT,
)
