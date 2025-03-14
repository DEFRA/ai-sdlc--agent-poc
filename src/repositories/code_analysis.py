"""Code analysis repository module."""

import logging
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.database.mongodb import COLLECTION_CODE_ANALYSIS, MongoDB
from src.models.code_analysis import (
    CodeAnalysisCreate,
    CodeAnalysisInDB,
    CodeAnalysisUpdate,
)

logger = logging.getLogger(__name__)


class CodeAnalysisRepository:
    """Repository for code analysis operations."""

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Get the code analysis collection."""
        return MongoDB.get_collection(COLLECTION_CODE_ANALYSIS)

    @staticmethod
    def _map_db_to_model(db_obj: dict) -> CodeAnalysisInDB:
        """Map database object to model."""
        if not db_obj:
            db_obj_empty_error = "Database object is None or empty"
            raise ValueError(db_obj_empty_error)

        # Convert ObjectId to string
        db_obj["id"] = str(db_obj.pop("_id"))
        return CodeAnalysisInDB(**db_obj)

    async def create(self, obj_in: CodeAnalysisCreate) -> CodeAnalysisInDB:
        """
        Create a new code analysis document in the database.

        Args:
            obj_in: The code analysis object to create.

        Returns:
            The created code analysis document.
        """
        collection = self._get_collection()

        # Convert to dict and prepare for MongoDB
        obj_dict = obj_in.model_dump()

        try:
            result = await collection.insert_one(obj_dict)
            # Get the created document
            created_doc = await collection.find_one({"_id": result.inserted_id})
            return self._map_db_to_model(created_doc)
        except Exception as e:
            logger.error("Error creating code analysis: %s", e)
            raise

    async def get(self, analysis_id: str) -> Optional[CodeAnalysisInDB]:
        """
        Get a code analysis document by ID.

        Args:
            analysis_id: The ID of the document to retrieve.

        Returns:
            The code analysis document if found, None otherwise.

        Raises:
            InvalidId: If the analysis_id is not a valid ObjectId.
        """
        collection = self._get_collection()
        try:
            result = await collection.find_one({"_id": ObjectId(analysis_id)})
            if result:
                return self._map_db_to_model(result)
            return None
        except InvalidId as e:
            logger.error(
                "Invalid ObjectId format for analysis_id %s: %s", analysis_id, e
            )
            # Re-raise the exception so it can be handled properly in the API layer
            raise
        except Exception as e:
            logger.error(
                "Error retrieving code analysis with ID %s: %s", analysis_id, e
            )
            raise

    async def update(
        self, analysis_id: str, obj_in: CodeAnalysisUpdate
    ) -> Optional[CodeAnalysisInDB]:
        """
        Update a code analysis document.

        Args:
            analysis_id: The ID of the document to update.
            obj_in: The update data.

        Returns:
            The updated code analysis document if found, None otherwise.
        """
        collection = self._get_collection()

        # Only include non-None fields in the update
        update_data = {
            k: v
            for k, v in obj_in.model_dump(exclude_unset=True).items()
            if v is not None
        }

        if not update_data:
            # No fields to update
            return await self.get(analysis_id)

        try:
            await collection.update_one(
                {"_id": ObjectId(analysis_id)}, {"$set": update_data}
            )
            return await self.get(analysis_id)
        except Exception as e:
            logger.error("Error updating code analysis with ID %s: %s", analysis_id, e)
            raise

    async def list(
        self,
        filters: dict[str, Any] = None,
    ) -> list[CodeAnalysisInDB]:
        """
        List code analysis documents with filtering.

        Args:
            filters: Optional dictionary of filter conditions

        Returns:
            List of code analysis documents matching the criteria
        """
        collection = self._get_collection()

        # Use empty dict if no filters provided
        query_filters = filters or {}

        try:
            # Sort by creation date descending (newest first)
            cursor = collection.find(query_filters).sort("created_at", -1)

            # Convert cursor to list of documents
            documents = await cursor.to_list(length=None)

            # Map documents to model objects
            return [self._map_db_to_model(doc) for doc in documents]
        except Exception as e:
            logger.error("Error listing code analyses: %s", e)
            raise


# Create a singleton instance
code_analysis_repository = CodeAnalysisRepository()
