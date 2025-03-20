"""Architecture Documentation Node for the code analysis workflow."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

# Template for generating architecture documentation
ARCHITECTURE_DOCUMENTATION_TEMPLATE = """
You are an expert software architect tasked with documenting the architecture of a codebase.

You have been provided with information about the repository in the <repository_information> tag.

<repository_information>
{ingested_repository}
</repository_information>

Based on this information, generate a comprehensive architecture document that includes:

1. An overview of the system
2. The architectural style and patterns used
3. Component structure and dependencies
4. Data flow diagrams (described in text)
5. Implementation details and technology stack
6. Potential improvements and recommendations

The documentation should be in markdown format and should be detailed yet concise.
"""


async def architecture_documentation_node(
    state: CodeAnalysisState,
) -> CodeAnalysisState:
    """
    Architecture Documentation Node for the code analysis workflow.

    This node generates architecture documentation based on the ingested repository data.
    It uses a language model to analyze the repository and generate the documentation.

    Args:
        state: The current state of the workflow.

    Returns:
        Updated state with architecture documentation.
    """
    logger.info(
        "Starting Architecture Documentation Node for repository: %s",
        state.repository_url,
    )

    # Check if we have the required data
    if not state.ingested_repository:
        state.status = CodeAnalysisStatus.ERROR
        state.error = (
            "No ingested repository data available for architecture documentation"
        )

        # Update the database record
        if state.analysis_id:
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        return state

    try:
        # Prepare technologies for the prompt
        technologies_text = "\n".join(
            [f"- {tech}" for tech in (state.technologies or [])]
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(ARCHITECTURE_DOCUMENTATION_TEMPLATE)

        # Initialize the language model
        model = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

        # Prepare messages
        messages = prompt.format_messages(
            ingested_repository=state.ingested_repository,
            technologies=technologies_text or "No specific technologies identified.",
        )

        # Generate documentation
        response = await model.ainvoke(messages)
        architecture_documentation = response.content

        # Update state with architecture documentation
        state.architecture_documentation = architecture_documentation
        state.status = CodeAnalysisStatus.COMPLETED

        # Update the database record
        if state.analysis_id:
            update_data = CodeAnalysisUpdate(
                architecture_documentation=architecture_documentation,
                status=CodeAnalysisStatus.COMPLETED,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        logger.info(
            "Architecture Documentation Node completed successfully for repository: %s",
            state.repository_url,
        )

        return state
    except Exception as e:
        logger.error("Error in Architecture Documentation Node: %s", e)

        # Update state with error
        state.status = CodeAnalysisStatus.ERROR
        state.error = f"Architecture documentation generation failed: {str(e)}"

        # Update the database record
        if state.analysis_id:
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        return state
