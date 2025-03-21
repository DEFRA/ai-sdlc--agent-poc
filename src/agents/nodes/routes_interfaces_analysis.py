"""Routes and Interfaces Analysis Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.analysis_node_factory import create_analysis_node

logger = logging.getLogger(__name__)

# System message for the routes and interfaces analysis agent
ROUTES_INTERFACES_ANALYSIS_SYSTEM_MESSAGE = """
You are an API and interface architect tasked with analyzing routes, APIs, and user interfaces in a codebase.

You have been provided with a list of route and interface related files that you need to analyze.
You should use the retrieve_files tool to get the content of these files.
"""

# Template for routes and interfaces analysis prompt
ROUTES_INTERFACES_ANALYSIS_PROMPT = """
Analyze the routes, APIs, and user interfaces in the following files from repository {repository_url}:

Files: {file_list}

---

Once you have the file contents, generate a comprehensive routes and interfaces analysis document that includes:

1. API Architecture Overview
   - High-level description of the API architecture
   - REST/GraphQL/RPC approach used
   - Authentication and authorization mechanisms

2. Endpoint Documentation
   - List of all endpoints/routes
   - HTTP methods supported (GET, POST, PUT, DELETE, etc.)
   - URL parameters and query parameters
   - Request and response schemas

3. UI Components and Navigation
   - Structure of the user interface
   - Main components and their purposes
   - Navigation flows and routing

4. Request/Response Flow
   - How requests are processed through the system
   - Middleware and interceptors
   - Error handling and response formatting

5. API/UI Interface Diagram
   - Create a diagram showing the relationship between endpoints and components
   - Use mermaid.js syntax for the diagram

Format the output in markdown, with diagrams in mermaid code blocks.
"""

# Create the routes and interfaces analysis node using the factory
routes_interfaces_analysis_node = create_analysis_node(
    analysis_type="Routes and Interfaces",
    input_field_name="routes_interfaces_files",
    output_field_name="routes_interfaces_analysis",
    system_message=ROUTES_INTERFACES_ANALYSIS_SYSTEM_MESSAGE,
    prompt_template=ROUTES_INTERFACES_ANALYSIS_PROMPT,
)
