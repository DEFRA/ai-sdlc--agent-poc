"""Data Model Identification Node for the code analysis workflow."""

import logging
from datetime import datetime, timezone

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)


# Define Pydantic model for structured output
class DataModelFiles(BaseModel):
    """Structure for data model files identified in the repository."""

    files: list[str] = Field(
        description="List of file paths that contain data models, schemas, or data persistence logic"
    )


# Template for identifying data model files
DATA_MODEL_IDENTIFICATION_TEMPLATE = """
You are an expert software architect tasked with identifying all files in a codebase that are related to data models.

You have been provided with information about the repository in the <repository_information> tag.

<repository_information>
{ingested_repository}
</repository_information>

Analyze the repository content and identify all files that:
1. Define data models or schemas
2. Handle data persistence (database operations, ORM mappings)
3. Expose data models via external interfaces (API endpoints, GraphQL schemas)

Return a list of file paths. Each path should be a valid file path from the repository.
"""


async def data_model_identification_node(
    state: CodeAnalysisState,
) -> CodeAnalysisState:
    """
    Data Model Identification Node for the code analysis workflow.

    This node identifies all files in the repository that are related to data models,
    including model definitions, persistence layers, and external interfaces.

    Args:
        state: The current state of the workflow.

    Returns:
        Updated state with identified data model files.
    """
    logger.info(
        "Starting Data Model Identification Node for repository: %s",
        state.repository_url,
    )

    # Check if we have the required data
    if not state.ingested_repository:
        state.status = CodeAnalysisStatus.ERROR
        state.error = (
            "No ingested repository data available for data model identification"
        )

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

    try:
        # Create prompt
        prompt = ChatPromptTemplate.from_template(DATA_MODEL_IDENTIFICATION_TEMPLATE)

        # Initialize the language model with structured output
        model = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

        # Configure the model to return structured output
        structured_model = model.with_structured_output(DataModelFiles)

        # Prepare messages
        messages = prompt.format_messages(
            ingested_repository=state.ingested_repository,
        )

        # Generate structured response
        structured_response = await structured_model.ainvoke(messages)

        # Extract file list from structured response
        data_model_files = structured_response.files

        # Update state with identified files and timestamp
        state.data_model_files = data_model_files

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                data_model_files=data_model_files,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_analysis=current_doc.data_model_analysis
                if current_doc
                else None,
                status=current_doc.status if current_doc else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

            # Log the database update
            logger.info(
                "Updated MongoDB with %d identified data model files for analysis ID: %s",
                len(data_model_files),
                state.analysis_id,
            )

        logger.info(
            "Data Model Identification Node completed successfully for repository: %s",
            state.repository_url,
        )

        return state
    except Exception as e:
        logger.error("Error in Data Model Identification Node: %s", e)

        # Update state with error and timestamp
        state.status = CodeAnalysisStatus.ERROR
        error_msg = f"Data model identification failed: {str(e)}"
        state.error = error_msg

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
