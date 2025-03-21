"""Data Model Identification Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.identification_node_factory import (
    create_identification_node,
)

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


# Create the data model identification node using the factory
data_model_identification_node = create_identification_node(
    prompt_template=DATA_MODEL_IDENTIFICATION_TEMPLATE,
    state_field_name="data_model_files",
)
