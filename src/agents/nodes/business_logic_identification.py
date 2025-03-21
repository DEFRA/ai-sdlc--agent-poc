"""Business Logic Identification Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.identification_node_factory import (
    create_identification_node,
)

logger = logging.getLogger(__name__)

# Template for identifying business logic files
BUSINESS_LOGIC_IDENTIFICATION_TEMPLATE = """
You are an expert software architect tasked with identifying all files in a codebase that contain business logic, relationships, dependencies, and tests.

You have been provided with information about the repository in the <repository_information> tag.

<repository_information>
{ingested_repository}
</repository_information>

Analyze the repository content and identify all files that:
1. Implement core business rules and logic
2. Define service layers or business operations
3. Handle application workflows and processes
4. Contain business validations and constraints
5. Define domain objects and their behavior
6. Implement business calculations or algorithms
7. Contain unit, integration, or functional tests for business features
8. Define interfaces, abstract classes, or base classes for business components
9. Implement dependency injection or service location patterns

Return a list of file paths. Each path should be a valid file path from the repository.
"""


# Create the business logic identification node using the factory
business_logic_identification_node = create_identification_node(
    prompt_template=BUSINESS_LOGIC_IDENTIFICATION_TEMPLATE,
    state_field_name="business_logic_files",
)
