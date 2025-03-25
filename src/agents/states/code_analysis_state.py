"""State models for the code analysis workflow."""

from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field

from src.models.code_analysis import CodeAnalysisStatus


def keep_non_none_reducer(a: Optional[Any], b: Optional[Any]) -> Any:
    """
    A reducer that keeps value a unless b is not None.
    Used for fields that shouldn't have concurrent updates.

    Args:
        a: Original value
        b: New value

    Returns:
        b if b is not None, otherwise a
    """
    return b if b is not None else a


def extend_list_reducer(
    a: Optional[list[Any]], b: Optional[list[Any]]
) -> Optional[list[Any]]:
    """
    A reducer that extends lists or returns the non-None value.

    Args:
        a: Original list
        b: New list

    Returns:
        Extended list or non-None value
    """
    if a is None:
        return b
    if b is None:
        return a
    return a + b


def error_reducer(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """
    A reducer that combines error messages.

    Args:
        a: Original error message
        b: New error message

    Returns:
        Combined error message
    """
    if a is None:
        return b
    if b is None:
        return a
    return f"{a}; {b}"


class CodeAnalysisState(BaseModel):
    """
    State model for the code analysis workflow.

    This model defines the state that is passed between nodes
    in the LangGraph workflow.
    """

    # Input - read-only values, should not be modified by nodes
    repository_url: Annotated[str, keep_non_none_reducer] = Field(
        ..., description="URL of the repository to analyze"
    )
    analysis_id: Annotated[Optional[str], keep_non_none_reducer] = Field(
        default=None, description="MongoDB document ID for the analysis"
    )

    # Internal state - these can be updated
    status: Annotated[CodeAnalysisStatus, keep_non_none_reducer] = Field(
        default=CodeAnalysisStatus.IN_PROGRESS, description="Status of the analysis"
    )
    ingested_repository: Annotated[Optional[str], keep_non_none_reducer] = Field(
        default=None, description="The ingested repository data"
    )
    technologies: Annotated[Optional[list[str]], extend_list_reducer] = Field(
        default=None, description="List of technologies used in the repository"
    )

    # Data Model Analysis
    data_model_files: Annotated[Optional[list[str]], keep_non_none_reducer] = Field(
        default=None, description="List of identified data model files"
    )
    data_model_analysis: Annotated[Optional[str], keep_non_none_reducer] = Field(
        default=None, description="Generated data model analysis with ERD"
    )

    # Routes and Interfaces Analysis
    routes_interfaces_files: Annotated[Optional[list[str]], keep_non_none_reducer] = (
        Field(
            default=None, description="List of identified routes and interfaces files"
        )
    )
    routes_interfaces_analysis: Annotated[Optional[str], keep_non_none_reducer] = Field(
        default=None, description="Generated routes and interfaces analysis"
    )

    # Output
    architecture_documentation: Annotated[Optional[str], keep_non_none_reducer] = Field(
        default=None, description="Generated architecture documentation"
    )

    # Error handling - combine errors from different branches
    error: Annotated[Optional[str], error_reducer] = Field(
        default=None, description="Error message if the workflow fails"
    )
