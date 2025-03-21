"""Repository Ingest Node for the code analysis workflow."""

import logging

import aiohttp

from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)


async def repository_ingest_node(state):
    """
    Repository Ingest Node for the code analysis workflow.

    This node calls the external Repository Ingest API to ingest the repository data.
    It updates the state with the ingested repository data and technologies.

    Args:
        state: The current state of the workflow (TypedDict).

    Returns:
        Updated state dictionary with repository data and technologies.
    """
    repository_url = state.get("repository_url")
    analysis_id = state.get("analysis_id")

    logger.info("Starting Repository Ingest Node for repository: %s", repository_url)

    try:
        # Call the external Repository Ingest API
        if not settings.REPOSITORY_INGEST_API_URL:
            error_msg = (
                "REPOSITORY_INGEST_API_URL is not set in the environment variables"
            )
            raise ValueError(error_msg)

        # Using the correct endpoint path
        repository_ingest_url = (
            f"{settings.REPOSITORY_INGEST_API_URL}/api/v1/repo-ingest"
        )

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                repository_ingest_url,
                json={"repositoryUrl": repository_url},
                headers={"Content-Type": "application/json"},
            ) as response,
        ):
            if response.status != 200:
                error_text = await response.text()
                logger.error(
                    "Repository Ingest API failed with status %s: %s",
                    response.status,
                    error_text,
                )
                api_error_msg = f"Repository Ingest API failed: {error_text}"
                raise ValueError(api_error_msg)

            result = await response.json()

            # Get repository data from API response
            ingested_repository = result.get("ingestedRepository")
            technologies = result.get("technologies", [])

            # Update the database record if we have an analysis_id
            if analysis_id:
                update_data = CodeAnalysisUpdate(
                    ingested_repository=ingested_repository,
                    technologies=technologies,
                )
                await code_analysis_repository.update(analysis_id, update_data)

            logger.info(
                "Repository Ingest Node completed successfully for repository: %s",
                repository_url,
            )

            # Return only the updated fields
            return {
                "ingested_repository": ingested_repository,
                "technologies": technologies,
            }
    except Exception as e:
        logger.error("Error in Repository Ingest Node: %s", e)

        error_msg = f"Repository ingest failed: {str(e)}"

        # Update the database record if we have an analysis_id
        if analysis_id:
            # Create update data
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
            )
            await code_analysis_repository.update(analysis_id, update_data)

        # Return only the error field, not the status field, to avoid conflicts
        return {"error": error_msg}
