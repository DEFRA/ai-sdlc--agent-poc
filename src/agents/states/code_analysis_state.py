"""State models for the code analysis workflow."""

from typing import Optional

from pydantic import BaseModel, Field

from src.models.code_analysis import CodeAnalysisStatus


class CodeAnalysisState(BaseModel):
    """
    State model for the code analysis workflow.

    This model defines the state that is passed between nodes
    in the LangGraph workflow.
    """

    # Input
    repository_url: str = Field(..., description="URL of the repository to analyze")

    # Internal state
    status: CodeAnalysisStatus = Field(
        default=CodeAnalysisStatus.IN_PROGRESS, description="Status of the analysis"
    )
    ingested_repository: Optional[str] = Field(
        default=None, description="The ingested repository data"
    )
    technologies: Optional[list[str]] = Field(
        default=None, description="List of technologies used in the repository"
    )

    # Data Model Analysis - Using Annotated for fields that might be updated concurrently
    data_model_files: Optional[list[str]] = Field(
        default=None, description="List of identified data model files"
    )
    data_model_analysis: Optional[str] = Field(
        default=None, description="Generated data model analysis with ERD"
    )

    # Routes and Interfaces Analysis - Using Annotated for fields that might be updated concurrently
    routes_interfaces_files: Optional[list[str]] = Field(
        default=None, description="List of identified routes and interfaces files"
    )
    routes_interfaces_analysis: Optional[str] = Field(
        default=None, description="Generated routes and interfaces analysis"
    )

    # Business Logic Analysis - Using Annotated for fields that might be updated concurrently
    business_logic_files: Optional[list[str]] = Field(
        default=None, description="List of identified business logic files"
    )
    business_logic_analysis: Optional[str] = Field(
        default=None, description="Generated business logic analysis"
    )

    # Product Requirements
    product_requirements: Optional[str] = Field(
        default=None, description="Generated product requirements document"
    )

    # Output
    architecture_documentation: Optional[str] = Field(
        default=None, description="Generated architecture documentation"
    )

    # Database reference
    analysis_id: Optional[str] = Field(
        default=None, description="MongoDB document ID for the analysis"
    )

    # Error handling
    error: Optional[str] = Field(
        default=None, description="Error message if the workflow fails"
    )
