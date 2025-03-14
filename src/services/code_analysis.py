"""Code analysis service module."""

import asyncio
import logging
from typing import Optional

from bson.errors import InvalidId

from src.agents.code_analysis_graph import run_code_analysis_workflow
from src.models.code_analysis import (
    CodeAnalysisCreate,
    CodeAnalysisInDB,
    CodeAnalysisStatus,
    CodeAnalysisUpdate,
)
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """Service for code analysis operations."""

    async def create_code_analysis(self, repository_url: str) -> CodeAnalysisInDB:
        """
        Create a new code analysis.

        Args:
            repository_url: The URL of the repository to analyze.

        Returns:
            The created code analysis.
        """
        try:
            # Create the code analysis document
            code_analysis_create = CodeAnalysisCreate(
                repository_url=repository_url,
                status=CodeAnalysisStatus.IN_PROGRESS,
            )

            # Create the code analysis in the database
            code_analysis = await code_analysis_repository.create(code_analysis_create)

            # Trigger the LangGraph workflow asynchronously
            asyncio.create_task(
                self._run_analysis_workflow(code_analysis.id, repository_url)
            )

            return code_analysis
        except Exception as e:
            logger.error("Error creating code analysis: %s", e)
            raise

    async def _run_analysis_workflow(
        self, analysis_id: str, repository_url: str
    ) -> None:
        """
        Run the code analysis workflow asynchronously.

        This method is called after creating a code analysis document.
        It runs the LangGraph workflow to analyze the repository.

        Args:
            analysis_id: The ID of the code analysis document.
            repository_url: The URL of the repository to analyze.
        """
        logger.info("Starting code analysis workflow for analysis ID: %s", analysis_id)

        try:
            # Run the LangGraph workflow
            await run_code_analysis_workflow(repository_url, analysis_id)

            logger.info(
                "Code analysis workflow completed for analysis ID: %s", analysis_id
            )
        except Exception as e:
            logger.error("Error running code analysis workflow: %s", e)

            # Update the code analysis status to ERROR
            try:
                update_data = CodeAnalysisUpdate(
                    status=CodeAnalysisStatus.ERROR,
                )
                await code_analysis_repository.update(analysis_id, update_data)
            except Exception as update_error:
                logger.error(
                    "Error updating code analysis status after workflow failure: %s",
                    update_error,
                )

    async def get_code_analysis(self, analysis_id: str) -> Optional[CodeAnalysisInDB]:
        """
        Get a code analysis by ID.

        Args:
            analysis_id: The ID of the code analysis.

        Returns:
            The code analysis if found, None otherwise.

        Raises:
            InvalidId: If the analysis_id is not a valid ObjectId.
        """
        try:
            return await code_analysis_repository.get(analysis_id)
        except InvalidId:
            # Re-raise the exception so it can be handled properly in the API layer
            raise
        except Exception as e:
            logger.error(
                "Error retrieving code analysis with ID %s: %s", analysis_id, e
            )
            raise

    async def update_code_analysis(
        self, analysis_id: str, obj_in: CodeAnalysisUpdate
    ) -> Optional[CodeAnalysisInDB]:
        """
        Update a code analysis.

        Args:
            analysis_id: The ID of the code analysis.
            obj_in: The update data.

        Returns:
            The updated code analysis if found, None otherwise.
        """
        try:
            return await code_analysis_repository.update(analysis_id, obj_in)
        except Exception as e:
            logger.error("Error updating code analysis with ID %s: %s", analysis_id, e)
            raise

    async def list_code_analyses(
        self,
        status: Optional[CodeAnalysisStatus] = None,
    ) -> list[CodeAnalysisInDB]:
        """
        List code analyses with optional filtering.

        Args:
            status: Optional status filter

        Returns:
            List of code analyses matching the criteria
        """
        try:
            # Create filter dict based on provided parameters
            filters = {}
            if status:
                filters["status"] = status

            return await code_analysis_repository.list(filters=filters)
        except Exception as e:
            logger.error("Error listing code analyses: %s", e)
            raise


# Create a singleton instance
code_analysis_service = CodeAnalysisService()
