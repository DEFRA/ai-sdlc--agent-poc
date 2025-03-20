"""Data Model Analysis ReAct agent setup."""

import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.tools.repo_tools import repo_tools
from src.config.settings import settings

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


def create_data_model_agent():
    """
    Create a ReAct agent for data model analysis.

    Returns:
        Configured ReAct agent
    """
    try:
        # Initialize the model with system message
        model = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=64000,
        ).bind(system_message=DATA_MODEL_ANALYSIS_SYSTEM_MESSAGE)

        # Bind tools to the model
        model_with_tools = model.bind_tools(repo_tools)

        # Create the ReAct agent
        agent = create_react_agent(model_with_tools, repo_tools)

        logger.info("Successfully created Data Model Analysis ReAct agent")
        return agent
    except Exception as e:
        logger.error("Error creating Data Model Analysis ReAct agent: %s", e)
        raise


async def run_data_model_agent(
    agent, repository_url: str, data_model_files: list[str]
) -> str:
    """
    Run the data model analysis agent on the specified repository and files.

    Args:
        agent: The configured ReAct agent
        repository_url: URL of the repository
        data_model_files: List of data model file paths to analyze

    Returns:
        Data model analysis report
    """
    try:
        # Create message for the agent
        file_list = "\n".join([f"- {file}" for file in data_model_files])

        message = HumanMessage(
            content=DATA_MODEL_ANALYSIS_PROMPT.format(
                repository_url=repository_url, file_list=file_list
            )
        )

        # Invoke the agent
        response = await agent.ainvoke({"messages": [message]})

        # Log the full response for debugging
        logger.debug(
            "Full agent response: %s",
            json.dumps(
                {
                    "messages": [
                        {
                            "type": type(msg).__name__,
                            "content": str(msg)[:500],  # Truncate for log readability
                        }
                        for msg in response["messages"]
                    ]
                },
                indent=2,
            ),
        )

        # Extract final message
        final_message = next(
            (
                msg
                for msg in reversed(response["messages"])
                if isinstance(msg, AIMessage)
            ),
            None,
        )

        if not final_message:
            error_msg = "No response from agent"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        # Log the final analysis result
        logger.info(
            "Data model analysis completed. Result length: %d characters",
            len(final_message.content),
        )

        # Return the agent's analysis
        return final_message.content
    except Exception as e:
        logger.error("Error running Data Model Analysis ReAct agent: %s", e)
        return f"Error in data model analysis: {str(e)}"
