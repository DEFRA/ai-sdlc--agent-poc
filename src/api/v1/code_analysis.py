"""Code analysis API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from src.models.code_analysis import CodeAnalysisRequest, CodeAnalysisResponse
from src.services.code_analysis import code_analysis_service

router = APIRouter(prefix="/code-analysis", tags=["code-analysis"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new code analysis request",
    description="Creates a new code analysis request and returns its ID",
)
async def create_code_analysis(request: CodeAnalysisRequest) -> dict[str, str]:
    """
    Create a new code analysis request.

    Args:
        request: The code analysis request.

    Returns:
        A dictionary containing the ID of the created code analysis.

    Raises:
        HTTPException: If there's an error creating the code analysis.
    """
    try:
        # Create the code analysis
        code_analysis = await code_analysis_service.create_code_analysis(
            repository_url=str(request.repository_url)
        )

        # Return the ID of the created code analysis
        return {"_id": code_analysis.id}
    except ValidationError as e:
        logger.error("Validation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {e}",
        ) from e
    except Exception as e:
        logger.error("Error creating code analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the code analysis request",
        ) from e


@router.get(
    "/{analysis_id}",
    response_model=CodeAnalysisResponse,
    summary="Get a code analysis by ID",
    description="Retrieves a code analysis by its ID",
)
async def get_code_analysis(analysis_id: str) -> CodeAnalysisResponse:
    """
    Get a code analysis by ID.

    Args:
        analysis_id: The ID of the code analysis.

    Returns:
        The code analysis.

    Raises:
        HTTPException: If the code analysis is not found or there's an error retrieving it.
    """
    try:
        code_analysis = await code_analysis_service.get_code_analysis(analysis_id)
        if not code_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Code analysis with ID {analysis_id} not found",
            )

        # Convert the model to the response model
        return CodeAnalysisResponse(
            id=code_analysis.id,
            repository_url=code_analysis.repository_url,
            status=code_analysis.status,
            architecture_documentation=code_analysis.architecture_documentation,
            ingested_repository=code_analysis.ingested_repository,
            technologies=code_analysis.technologies,
            created_at=code_analysis.created_at,
            updated_at=code_analysis.updated_at,
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error retrieving code analysis with ID %s: %s", analysis_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the code analysis with ID {analysis_id}",
        ) from e
