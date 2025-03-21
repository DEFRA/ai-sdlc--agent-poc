"""LLM Node Factory for creating reusable LangGraph nodes."""

import logging
from datetime import datetime, timezone
from typing import Any, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Constants
REPOSITORY_FIELD_NAME = "ingested_repository"


# Simple output model for file identification
class Files(BaseModel):
    """Model for file identification results."""

    files: list[str] = Field(
        description="List of file paths identified in the repository"
    )


# Token usage tracking callback
class TokenUsageCallbackHandler(BaseCallbackHandler):
    """Callback handler for tracking token usage."""

    def __init__(self):
        super().__init__()
        self.tokens = {"usage": None}

    def on_llm_end(self, response: Any, **_) -> None:
        """Called when the LLM ends processing, capturing token usage."""
        try:
            # Try to extract usage information
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                self.tokens["usage"] = response.usage_metadata
            elif (
                hasattr(response, "generation_info")
                and response.generation_info
                and "token_usage" in response.generation_info
            ):
                self.tokens["usage"] = response.generation_info["token_usage"]
            elif hasattr(response, "llm_output") and response.llm_output:
                if "token_usage" in response.llm_output:
                    self.tokens["usage"] = response.llm_output["token_usage"]
                elif "usage" in response.llm_output:
                    self.tokens["usage"] = response.llm_output["usage"]
            # For Anthropic responses
            elif (
                hasattr(response, "response_metadata")
                and response.response_metadata
                and "usage" in response.response_metadata
            ):
                self.tokens["usage"] = response.response_metadata["usage"]
        except Exception as e:
            logger.warning("Error capturing token usage: %s", e)


async def _update_db_with_result(
    state: CodeAnalysisState, result: Any, field_name: str
) -> None:
    """Helper function to update database with analysis results."""
    current_doc = await code_analysis_repository.get(state.analysis_id)

    # Create update data with the result field dynamically
    update_data = CodeAnalysisUpdate(
        updated_at=datetime.now(timezone.utc),
    )

    # Set the field dynamically
    setattr(update_data, field_name, result)

    # Preserve existing fields from current_doc, not from state
    # This avoids trying to copy fields that don't exist in CodeAnalysisUpdate
    if current_doc:
        # Get the field names from the CodeAnalysisUpdate model
        valid_fields = set(CodeAnalysisUpdate.model_fields.keys())

        # Only copy fields that exist in the CodeAnalysisUpdate model
        for field in valid_fields:
            # Skip fields we've already set
            if field not in ["updated_at", field_name] and hasattr(current_doc, field):
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


def create_identification_node(
    prompt_template: str,
    state_field_name: str,
    model_name: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0,
):
    """
    Factory function that creates an identification node.
    Identification nodes are used to identify files in a repository.
    A lot of the behavior of the identification nodes is the same, so we use this factory to create them.

    Args:
        prompt_template: The prompt template string to use for the LLM
        state_field_name: Field name in state to store results
        model_name: LLM model to use
        temperature: Temperature setting for the LLM

    Returns:
        An async function that can be used as a LangGraph node
    """

    async def identification_node(state: CodeAnalysisState) -> CodeAnalysisState:
        """
        Identification node created by the factory.

        Args:
            state: The current state of the workflow

        Returns:
            Updated state with identified files
        """
        logger.info(
            "Starting %s Node for repository: %s",
            state_field_name,
            state.repository_url,
        )

        # Check if we have the required data
        repository_data = getattr(state, REPOSITORY_FIELD_NAME, None)
        if not repository_data:
            state.status = CodeAnalysisStatus.ERROR
            state.error = (
                f"No {REPOSITORY_FIELD_NAME} data available for {state_field_name}"
            )

            # Update the database record
            if state.analysis_id:
                await _update_db_on_error(state)

            return state

        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)

            token_usage_callback = TokenUsageCallbackHandler()

            model = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                callbacks=[token_usage_callback],
            )

            # Configure the model to return structured output
            structured_model = model.with_structured_output(Files)

            messages = prompt.format_messages(
                ingested_repository=repository_data,
            )

            response = await structured_model.ainvoke(messages)

            file_list = response.files

            # Update state
            setattr(state, state_field_name, file_list)

            # Update the database record
            if state.analysis_id:
                await _update_db_with_result(state, file_list, state_field_name)

            logger.info(
                "%s Node completed successfully for repository: %s",
                state_field_name,
                state.repository_url,
            )

            return state
        except Exception as e:
            logger.error("Error in %s Node: %s", state_field_name, e)

            # Update state with error and timestamp
            state.status = CodeAnalysisStatus.ERROR
            error_msg = f"{state_field_name} failed: {str(e)}"
            state.error = error_msg

            # Update the database record
            if state.analysis_id:
                await _update_db_on_error(state)

            return state

    return identification_node
