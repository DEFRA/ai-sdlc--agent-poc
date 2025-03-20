"""Generic ReAct agent factory for creating analysis agents."""

import json
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.tools.repo_tools import repo_tools
from src.config.settings import settings

logger = logging.getLogger(__name__)


def create_analysis_agent(
    system_message: str,
    model_name: str = "claude-3-7-sonnet-20250219",
    temperature: float = 0,
    max_tokens: int = 64000,
) -> Any:
    """
    Create a ReAct agent for analysis.

    Args:
        system_message: System message for the agent
        model_name: Model name to use
        temperature: Temperature setting for generation
        max_tokens: Maximum tokens for generation

    Returns:
        Configured ReAct agent
    """
    try:
        # Initialize the model with system message
        model = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=max_tokens,
        ).bind(system_message=system_message)

        # Bind tools to the model
        model_with_tools = model.bind_tools(repo_tools)

        # Create the ReAct agent
        agent = create_react_agent(model_with_tools, repo_tools)

        logger.info("Successfully created analysis ReAct agent")
        return agent
    except Exception as e:
        logger.error("Error creating analysis ReAct agent: %s", e)
        raise


async def run_analysis_agent(
    agent: Any,
    prompt_template: str,
    repository_url: str,
    file_list: list[str],
) -> str:
    """
    Run the analysis agent on the specified repository and files.

    Args:
        agent: The configured ReAct agent
        prompt_template: The prompt template with {repository_url} and {file_list} placeholders
        repository_url: URL of the repository
        file_list: List of file paths to analyze

    Returns:
        Analysis report
    """
    try:
        # Format file list for prompt
        formatted_file_list = "\n".join([f"- {file}" for file in file_list])

        # Format the prompt
        formatted_prompt = prompt_template.format(
            repository_url=repository_url, file_list=formatted_file_list
        )

        # Create message for the agent
        message = HumanMessage(content=formatted_prompt)

        # Invoke the agent
        response = await agent.ainvoke({"messages": [message]})

        # Log the full response for debugging (truncated)
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
            "Analysis completed. Result length: %d characters",
            len(final_message.content),
        )

        # Return the agent's analysis
        return final_message.content
    except Exception as e:
        logger.error("Error running analysis ReAct agent: %s", e)
        return f"Error in analysis: {str(e)}"
