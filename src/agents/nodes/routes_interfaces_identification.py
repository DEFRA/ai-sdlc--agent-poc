"""Routes and Interfaces Identification Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.identification_node_factory import (
    create_identification_node,
)

logger = logging.getLogger(__name__)

# Template for identifying routes and interfaces files
ROUTES_INTERFACES_IDENTIFICATION_TEMPLATE = """
You are an expert software architect tasked with identifying all files in a codebase that are related to routes, user interfaces, and API interfaces.

You have been provided with information about the repository in the <repository_information> tag.

<repository_information>
{ingested_repository}
</repository_information>

Analyze the repository content and identify all files that:
1. Define API routes or endpoints
2. Contain API controllers or handlers
3. Define UI components, views, or templates
4. Handle HTTP requests and responses
5. Define GraphQL schemas or resolvers
6. Contain REST API definitions
7. Define URL routing or navigation
8. Implement frontend interfaces or UI layouts

Return a list of file paths. Each path should be a valid file path from the repository.
"""


# Create the routes and interfaces identification node using the factory
routes_interfaces_identification_node = create_identification_node(
    prompt_template=ROUTES_INTERFACES_IDENTIFICATION_TEMPLATE,
    state_field_name="routes_interfaces_files",
)
