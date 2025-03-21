"""Business Logic Analysis Node for the code analysis workflow."""

import logging

from src.agents.nodes.factory.analysis_node_factory import create_analysis_node

logger = logging.getLogger(__name__)

# System message for the business logic analysis agent
BUSINESS_LOGIC_ANALYSIS_SYSTEM_MESSAGE = """
You are a software architect tasked with analyzing business logic in a codebase.

You have been provided with a list of business logic related files that you need to analyze.
You should use the retrieve_files tool to get the content of these files.
"""

# Template for business logic analysis prompt
BUSINESS_LOGIC_ANALYSIS_PROMPT = """
Analyze the business logic in the following files from repository {repository_url}:

Files: {file_list}

---

Once you have the file contents, generate a comprehensive business logic analysis document that includes:

1. Domain Model Overview
   - High-level description of the domain
   - Key business concepts and their relationships
   - Business rules and constraints

2. Service Architecture
   - Core services and their responsibilities
   - Interactions between services
   - Dependency patterns and injection mechanisms

3. Business Workflow Analysis
   - Main business processes and workflows
   - Decision points and rules
   - Error handling and exception flows

4. Testing Strategy
   - Test coverage of business logic
   - Types of tests (unit, integration, functional)
   - Test patterns and frameworks used

5. Component Relationship Diagram
   - Create a mermaid.js diagram showing dependencies between components
   - Show class relationships and interactions
   - Highlight key interfaces and implementations

Format the output in markdown, with diagrams in mermaid code blocks.
"""

# Create the business logic analysis node using the factory
business_logic_analysis_node = create_analysis_node(
    analysis_type="Business Logic",
    input_field_name="business_logic_files",
    output_field_name="business_logic_analysis",
    system_message=BUSINESS_LOGIC_ANALYSIS_SYSTEM_MESSAGE,
    prompt_template=BUSINESS_LOGIC_ANALYSIS_PROMPT,
)
