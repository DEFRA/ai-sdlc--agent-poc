"""LLM Analysis Node Factory for creating reusable LangGraph nodes."""

import logging
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from src.agents.react_agents.analysis_agent import (
    create_analysis_agent,
    run_analysis_agent,
)
from src.agents.states.analysis_state import AnalysisState
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def _update_db_with_result(
    analysis_id: str, result: Any, field_name: str
) -> None:
    """Helper function to update database with analysis results."""
    if not analysis_id:
        logger.warning("No analysis_id provided, skipping database update")
        return

    # Create update data with just the result field and status
    update_data = CodeAnalysisUpdate(
        status=CodeAnalysisStatus.COMPLETED,
        updated_at=datetime.now(timezone.utc),
    )

    # Set the field dynamically
    setattr(update_data, field_name, result)

    await code_analysis_repository.update(analysis_id, update_data)

    logger.info(
        "Updated MongoDB with %s results for analysis ID: %s",
        field_name,
        analysis_id,
    )


async def _update_db_on_error(analysis_id: str, error_msg: str) -> None:
    """Helper function to update database on error."""
    if not analysis_id:
        logger.warning("No analysis_id provided, skipping database update")
        return

    # Create update with just the error and status fields
    update_data = CodeAnalysisUpdate(
        status=CodeAnalysisStatus.ERROR,
        updated_at=datetime.now(timezone.utc),
    )

    await code_analysis_repository.update(analysis_id, update_data)

    logger.error(
        "Updated error status for analysis ID: %s - %s", analysis_id, error_msg
    )


async def _handle_analysis(
    state: AnalysisState,
    config: dict[str, Any],
    agent: Any,
    analysis_type: str,
    input_field_name: str,
    output_field_name: str,
    prompt_template: str,
) -> AnalysisState:
    """Handle the analysis process and update state accordingly.

    Args:
        state: Current workflow state
        config: Configuration containing read-only context values
        agent: The analysis agent
        analysis_type: Type of analysis being performed
        input_field_name: Field in state containing input files
        output_field_name: Field in state to store results
        prompt_template: Template for the analysis prompt

    Returns:
        Updated state
    """
    # Extract context values from config
    node_config = config.get("configurable", {})
    analysis_id = node_config.get("analysis_id")
    repository_url = node_config.get("repository_url")

    # Check if we have the required data
    input_files = getattr(state, input_field_name, None)
    if not input_files:
        error_msg = f"No {input_field_name} identified for analysis"
        state.error = error_msg

        # Update the database record
        if analysis_id:
            await _update_db_on_error(analysis_id, error_msg)

        return state

    # Check if agent was initialized properly
    if agent is None:
        error_msg = f"{analysis_type} Analysis agent was not initialized properly"
        state.error = error_msg

        # Update the database record
        if analysis_id:
            await _update_db_on_error(analysis_id, error_msg)

        return state

    try:
        # Log the start of the agent analysis
        logger.info(
            "Initiating %s agent analysis for repository: %s with %d files",
            analysis_type,
            repository_url,
            len(input_files),
        )

        # Run the agent to analyze the files
        analysis_result = await run_analysis_agent(
            agent=agent,
            prompt_template=prompt_template,
            repository_url=str(repository_url),
            file_list=input_files,
        )

        # Log the result of the agent analysis
        if analysis_result.startswith("Error"):
            logger.error(
                "%s agent analysis failed with error: %s",
                analysis_type,
                analysis_result,
            )
            raise ValueError(analysis_result)

        logger.info(
            "%s agent analysis completed successfully. Analysis length: %d characters",
            analysis_type,
            len(analysis_result),
        )

        # Update state with analysis
        setattr(state, output_field_name, analysis_result)

        # Update the database record
        if analysis_id:
            await _update_db_with_result(
                analysis_id, analysis_result, output_field_name
            )

        logger.info(
            "%s Analysis Node completed successfully for repository: %s",
            analysis_type,
            repository_url,
        )

        return state
    except Exception as e:
        error_msg = f"{analysis_type} analysis failed: {str(e)}"
        logger.error("Error in %s Analysis Node: %s", analysis_type, e)

        # Update state with error
        state.error = error_msg

        # Update the database record
        if analysis_id:
            await _update_db_on_error(analysis_id, error_msg)

        return state


def create_analysis_node(
    analysis_type: str,
    input_field_name: str,
    output_field_name: str,
    system_message: str,
    prompt_template: str,
    model_name: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0,
) -> Callable[[AnalysisState, dict[str, Any]], Awaitable[AnalysisState]]:
    """
    Factory function that creates an analysis node.
    Analysis nodes use an agent to analyze files and generate reports.

    Args:
        analysis_type: A descriptive name for the analysis type
        input_field_name: Field name in state containing input files to analyze
        output_field_name: Field name in state to store analysis results
        system_message: System message for the agent
        prompt_template: Template for the analysis prompt
        model_name: Model name to use for analysis
        temperature: Temperature setting for generation

    Returns:
        An async function that can be used as a LangGraph node
    """

    # Initialize the agent at module level
    try:
        agent = create_analysis_agent(
            system_message=system_message,
            model_name=model_name,
            temperature=temperature,
        )
    except Exception as e:
        logger.error("Failed to initialize %s agent: %s", analysis_type, e)
        agent = None

    async def analysis_node(
        state: AnalysisState, config: dict[str, Any]
    ) -> AnalysisState:
        """Analysis node created by the factory."""
        # Extract context values from config
        node_config = config.get("configurable", {})
        repository_url = node_config.get("repository_url")

        logger.info(
            "Starting %s Analysis Node for repository: %s",
            analysis_type,
            repository_url,
        )

        return await _handle_analysis(
            state=state,
            config=config,
            agent=agent,
            analysis_type=analysis_type,
            input_field_name=input_field_name,
            output_field_name=output_field_name,
            prompt_template=prompt_template,
        )

    return analysis_node
