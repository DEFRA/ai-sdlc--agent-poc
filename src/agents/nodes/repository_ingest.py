"""Repository Ingest Node for the code analysis workflow."""

import logging

import aiohttp

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)


async def repository_ingest_node(state: CodeAnalysisState) -> CodeAnalysisState:
    """
    Repository Ingest Node for the code analysis workflow.

    This node calls the external Repository Ingest API to ingest the repository data.
    It updates the state with the ingested repository data and technologies.

    Args:
        state: The current state of the workflow.

    Returns:
        Updated state with repository data and technologies.
    """
    logger.info(
        "Starting Repository Ingest Node for repository: %s", state.repository_url
    )

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
                json={"repositoryUrl": state.repository_url},
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

            # Update state with repository data
            state.ingested_repository = result.get("ingestedRepository")
            state.technologies = result.get("technologies", [])

            # Update the database record
            if state.analysis_id:
                update_data = CodeAnalysisUpdate(
                    ingested_repository=state.ingested_repository,
                    technologies=state.technologies,
                )
                await code_analysis_repository.update(state.analysis_id, update_data)

            logger.info(
                "Repository Ingest Node completed successfully for repository: %s",
                state.repository_url,
            )

            return state
    except Exception as e:
        logger.error("Error in Repository Ingest Node: %s", e)

        # Update state with error
        state.status = CodeAnalysisStatus.ERROR
        state.error = f"Repository ingest failed: {str(e)}"

        # Update the database record
        if state.analysis_id:
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        return state
