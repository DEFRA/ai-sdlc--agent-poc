"""LLM Analysis Node Factory for creating reusable LangGraph nodes."""

import logging
from datetime import datetime, timezone
from typing import Any, TypeVar

from pydantic import BaseModel

from src.agents.react_agents.analysis_agent import (
    create_analysis_agent,
    run_analysis_agent,
)
from src.agents.states.code_analysis_state import CodeAnalysisState
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def _update_db_with_result(
    state: CodeAnalysisState, result: Any, field_name: str
) -> None:
    """Helper function to update database with analysis results."""
    current_doc = await code_analysis_repository.get(state.analysis_id)

    # Create update data with the result field dynamically
    update_data = CodeAnalysisUpdate(
        status=CodeAnalysisStatus.COMPLETED,
        updated_at=datetime.now(timezone.utc),
    )

    # Set the field dynamically
    setattr(update_data, field_name, result)

    # Preserve existing fields from current_doc, not from state
    if current_doc:
        # Get the field names from the CodeAnalysisUpdate model
        valid_fields = set(CodeAnalysisUpdate.model_fields.keys())

        # Only copy fields that exist in the CodeAnalysisUpdate model
        for field in valid_fields:
            # Skip fields we've already set
            if field not in ["updated_at", "status", field_name] and hasattr(
                current_doc, field
            ):
                value = getattr(current_doc, field, None)
                if value is not None:
                    setattr(update_data, field, value)

    await code_analysis_repository.update(state.analysis_id, update_data)

    logger.info(
        "Updated MongoDB with %s results for analysis ID: %s",
        field_name,
        state.analysis_id,
    )


async def _update_db_on_error(state: CodeAnalysisState) -> None:
    """Helper function to update database on error."""
    current_doc = await code_analysis_repository.get(state.analysis_id)

    # Create update with just the error fields
    update_data = CodeAnalysisUpdate(
        status=CodeAnalysisStatus.ERROR,
        error=state.error,
        updated_at=datetime.now(timezone.utc),
    )

    # Preserve existing fields from current_doc, not from state
    if current_doc:
        # Get the field names from the CodeAnalysisUpdate model
        valid_fields = set(CodeAnalysisUpdate.model_fields.keys())

        # Only copy fields that exist in the CodeAnalysisUpdate model
        for field in valid_fields:
            # Skip fields we've already set
            if field not in ["updated_at", "status", "error"] and hasattr(
                current_doc, field
            ):
                value = getattr(current_doc, field, None)
                if value is not None:
                    setattr(update_data, field, value)

    await code_analysis_repository.update(state.analysis_id, update_data)


async def _handle_analysis(
    state,
    agent: Any,
    analysis_type: str,
    input_field_name: str,
    output_field_name: str,
    prompt_template: str,
):
    """Handle the analysis process and update state accordingly.

    Args:
        state: The current state of the workflow (TypedDict)
        agent: The analysis agent to use
        analysis_type: A descriptive name for the analysis type
        input_field_name: Field name in state containing input files to analyze
        output_field_name: Field name in state to store analysis results
        prompt_template: Template for the analysis prompt

    Returns:
        Updated state dictionary with analysis or error
    """
    # First check if the agent is available
    if agent is None:
        error_message = "No agent available for " + analysis_type + " analysis"
        raise ValueError(error_message)

    repository_url = state.get("repository_url")
    analysis_id = state.get("analysis_id")

    # Check if we have the required input data
    input_files = state.get(input_field_name)
    if not input_files:
        # Return only the error field to avoid concurrent updates
        error_msg = f"No {input_field_name} data available for {analysis_type} analysis"

        # Update the database record if we have an analysis_id
        if analysis_id:
            # Create a temporary state object for DB update
            temp_state = CodeAnalysisState(
                repository_url=repository_url,
                analysis_id=analysis_id,
                status=CodeAnalysisStatus.ERROR,
                error=error_msg,
            )
            await _update_db_on_error(temp_state)

        return {"error": error_msg}

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

        # Update the database record if we have an analysis_id
        if analysis_id:
            # Create a temporary state object for DB update
            temp_state = CodeAnalysisState(
                repository_url=repository_url,
                analysis_id=analysis_id,
                status=CodeAnalysisStatus.COMPLETED,
            )
            await _update_db_with_result(temp_state, analysis_result, output_field_name)

        logger.info(
            "%s Analysis Node completed successfully for repository: %s",
            analysis_type,
            repository_url,
        )

        # Return only the updated field, no status to avoid concurrent updates
        return {output_field_name: analysis_result}
    except Exception as e:
        logger.error("Error in %s Analysis Node: %s", analysis_type, e)

        error_msg = f"{analysis_type} analysis failed: {str(e)}"

        # Update the database record if we have an analysis_id
        if analysis_id:
            # Create a temporary state object for DB update
            temp_state = CodeAnalysisState(
                repository_url=repository_url,
                analysis_id=analysis_id,
                status=CodeAnalysisStatus.ERROR,
                error=error_msg,
            )
            await _update_db_on_error(temp_state)

        # Return only the error field, no status to avoid concurrent updates
        return {"error": error_msg}


def create_analysis_node(
    analysis_type: str,
    input_field_name: str,
    output_field_name: str,
    system_message: str,
    prompt_template: str,
    model_name: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0,
):
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

    async def analysis_node(state):
        """Analysis node created by the factory."""
        repository_url = state.get("repository_url")
        logger.info(
            "Starting %s Analysis Node for repository: %s",
            analysis_type,
            repository_url,
        )

        return await _handle_analysis(
            state=state,
            agent=agent,
            analysis_type=analysis_type,
            input_field_name=input_field_name,
            output_field_name=output_field_name,
            prompt_template=prompt_template,
        )

    return analysis_node
