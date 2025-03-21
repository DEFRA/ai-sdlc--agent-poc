"""Code analysis models module."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CodeAnalysisStatus(str, Enum):
    """Status enum for code analysis."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""

    repository_url: HttpUrl = Field(..., description="URL of the repository to analyze")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""

    id: str = Field(..., description="The unique identifier for the code analysis")
    repository_url: HttpUrl = Field(..., description="URL of the repository to analyze")
    status: CodeAnalysisStatus = Field(
        ..., description="Current status of the analysis"
    )
    architecture_documentation: Optional[str] = Field(
        None, description="Architecture documentation in markdown or structured format"
    )
    ingested_repository: Optional[str] = Field(
        None, description="The ingested repository data"
    )
    technologies: Optional[list[str]] = Field(
        None, description="List of technologies used in the repository"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the analysis was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the analysis was last updated"
    )


class CodeAnalysisCreate(BaseModel):
    """Model for creating a code analysis in the database."""

    repository_url: str
    status: CodeAnalysisStatus = CodeAnalysisStatus.IN_PROGRESS
    architecture_documentation: Optional[str] = None
    ingested_repository: Optional[str] = None
    technologies: Optional[list[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CodeAnalysisUpdate(BaseModel):
    """Model for updating a code analysis in the database."""

    status: Optional[CodeAnalysisStatus] = None
    architecture_documentation: Optional[str] = None
    ingested_repository: Optional[str] = None
    technologies: Optional[list[str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CodeAnalysisInDB(CodeAnalysisCreate):
    """Database model for code analysis."""

    id: str
