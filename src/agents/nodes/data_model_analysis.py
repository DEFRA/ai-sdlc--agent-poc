"""Data Model Analysis Node for the code analysis workflow."""

import json
import logging
from datetime import datetime, timezone

from src.agents.react_agents.data_model_agent import (
    create_data_model_agent,
    run_data_model_agent,
)
from src.agents.states.code_analysis_state import CodeAnalysisState
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

# Create the ReAct agent at module level
try:
    data_model_agent = create_data_model_agent()
except Exception as e:
    logger.error("Failed to initialize Data Model Analysis agent: %s", e)
    data_model_agent = None


async def data_model_analysis_node(
    state: CodeAnalysisState,
) -> CodeAnalysisState:
    """
    Data Model Analysis Node for the code analysis workflow.

    This node uses a ReAct agent to analyze the identified data model files and generate
    a comprehensive report including an ERD diagram in mermaid format.

    Args:
        state: The current state of the workflow.

    Returns:
        Updated state with data model analysis report.
    """
    logger.info(
        "Starting Data Model Analysis Node for repository: %s",
        state.repository_url,
    )

    # Check if we have the required data
    if not state.data_model_files:
        state.status = CodeAnalysisStatus.ERROR
        state.error = "No data model files identified for analysis"

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
                error=state.error,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_files=current_doc.data_model_files if current_doc else None,
                data_model_analysis=current_doc.data_model_analysis
                if current_doc
                else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        return state

    # Check if agent was initialized properly
    if data_model_agent is None:
        state.status = CodeAnalysisStatus.ERROR
        state.error = "Data Model Analysis agent was not initialized properly"

        # Update the database record
        if state.analysis_id:
            await update_database_error(state)

        return state

    try:
        # Log the files to be analyzed with more detail
        logger.debug(
            "Data model files to be analyzed: %s",
            json.dumps(state.data_model_files, indent=2),
        )

        # Log the start of the ReAct agent analysis
        logger.info(
            "Initiating ReAct agent analysis for repository: %s with %d files",
            state.repository_url,
            len(state.data_model_files),
        )

        # Run the ReAct agent to analyze the data models
        data_model_analysis = await run_data_model_agent(
            data_model_agent,
            str(state.repository_url),
            state.data_model_files,
        )

        # Log the result of the agent analysis
        if data_model_analysis.startswith("Error"):
            logger.error(
                "ReAct agent analysis failed with error: %s", data_model_analysis
            )
            raise ValueError(data_model_analysis)
        logger.info(
            "ReAct agent analysis completed successfully. "
            "Analysis length: %d characters",
            len(data_model_analysis),
        )

        # Update state with analysis and timestamp
        state.data_model_analysis = data_model_analysis
        state.status = CodeAnalysisStatus.COMPLETED

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                data_model_analysis=data_model_analysis,
                status=CodeAnalysisStatus.COMPLETED,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_files=current_doc.data_model_files if current_doc else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

            # Log the database update
            logger.info(
                "Updated MongoDB with data model analysis for analysis ID: %s",
                state.analysis_id,
            )

        logger.info(
            "Data Model Analysis Node completed successfully for repository: %s",
            state.repository_url,
        )

        return state
    except Exception as e:
        logger.error("Error in Data Model Analysis Node: %s", e)

        # Update state with error and timestamp
        state.status = CodeAnalysisStatus.ERROR
        error_msg = f"Data model analysis failed: {str(e)}"
        state.error = error_msg

        # Update the database record
        if state.analysis_id:
            await update_database_error(state)

        return state


async def update_database_error(state: CodeAnalysisState) -> None:
    """
    Update the database with error information.

    Args:
        state: The current state containing error information
    """
    try:
        # Get current state from database to preserve other fields
        current_doc = await code_analysis_repository.get(state.analysis_id)
        update_data = CodeAnalysisUpdate(
            status=CodeAnalysisStatus.ERROR,
            error=state.error,
            updated_at=datetime.now(timezone.utc),
            # Preserve existing fields
            data_model_files=current_doc.data_model_files if current_doc else None,
            data_model_analysis=current_doc.data_model_analysis
            if current_doc
            else None,
        )
        await code_analysis_repository.update(state.analysis_id, update_data)
    except Exception as e:
        # Log the database update failure
        logger.error(
            "Failed to update MongoDB with error for analysis ID: %s. Error: %s",
            state.analysis_id,
            str(e),
        )
