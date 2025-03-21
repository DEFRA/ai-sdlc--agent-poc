"""Product Requirements Node for the code analysis workflow."""

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

# Template for product requirements generation
PRODUCT_REQUIREMENTS_TEMPLATE = """
You are a senior product manager tasked with creating a comprehensive product requirements document based on the technical analysis of a codebase.

You have been provided with three detailed analyses:

1. Data Model Analysis:
<data_model_analysis>
{data_model_analysis}
</data_model_analysis>

2. Routes and Interfaces Analysis:
<routes_interfaces_analysis>
{routes_interfaces_analysis}
</routes_interfaces_analysis>

3. Business Logic Analysis:
<business_logic_analysis>
{business_logic_analysis}
</business_logic_analysis>

Based on these analyses, create a detailed product requirements document that includes:

1. Executive Summary
   - High-level overview of the product
   - Key capabilities and value proposition
   - Target users and use cases

2. Product Vision
   - Long-term vision for the product
   - Alignment with business goals
   - Potential future enhancements

3. Feature Breakdown
   - Detailed list of features identified in the codebase
   - Categorization of features by domain area
   - Priority and importance of each feature

4. User Stories
   - User stories in the format "As a [user type], I want to [action], so that [benefit]"
   - Acceptance criteria for each user story
   - Dependencies between user stories

5. Non-Functional Requirements
   - Performance requirements
   - Security requirements
   - Scalability and reliability requirements

Format the output in markdown, with appropriate headers, lists, and tables.
"""


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

    # Preserve existing fields from current_doc
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

    # Preserve existing fields from current_doc
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


async def product_requirements_node(state):
    """
    Node that generates product requirements based on all previous analyses.

    Args:
        state: The current state of the workflow (TypedDict)

    Returns:
        Updated state dictionary with product requirements
    """
    repository_url = state.get("repository_url")
    analysis_id = state.get("analysis_id")

    logger.info("Starting Product Requirements Node for repository: %s", repository_url)

    # Check if we have all the required analyses
    data_model_analysis = state.get("data_model_analysis")
    routes_interfaces_analysis = state.get("routes_interfaces_analysis")
    business_logic_analysis = state.get("business_logic_analysis")

    if (
        not data_model_analysis
        or not routes_interfaces_analysis
        or not business_logic_analysis
    ):
        error_msg = (
            "Missing one or more required analyses for product requirements generation"
        )

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

        # Return only the error field
        return {"error": error_msg}

    try:
        # Create the prompt
        prompt = ChatPromptTemplate.from_template(PRODUCT_REQUIREMENTS_TEMPLATE)

        # Initialize the model
        model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

        # Format the messages
        messages = prompt.format_messages(
            data_model_analysis=data_model_analysis,
            routes_interfaces_analysis=routes_interfaces_analysis,
            business_logic_analysis=business_logic_analysis,
        )

        # Generate the product requirements
        response = await model.ainvoke(messages)
        product_requirements = response.content

        # Update the database record if we have an analysis_id
        if analysis_id:
            # Create a temporary state object for DB update
            temp_state = CodeAnalysisState(
                repository_url=repository_url,
                analysis_id=analysis_id,
                product_requirements=product_requirements,
                status=CodeAnalysisStatus.COMPLETED,
            )
            await _update_db_with_result(
                temp_state, product_requirements, "product_requirements"
            )

        logger.info(
            "Product Requirements Node completed successfully for repository: %s",
            repository_url,
        )

        # Return only the updated field
        return {"product_requirements": product_requirements}
    except Exception as e:
        logger.error("Error in Product Requirements Node: %s", e)

        error_msg = f"Product requirements generation failed: {str(e)}"

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

        # Return only the error field
        return {"error": error_msg}
