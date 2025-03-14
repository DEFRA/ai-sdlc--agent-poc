"""MongoDB connection module."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config.settings import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Connect to MongoDB.

        This method establishes a connection to MongoDB using the URI from settings
        and initializes the database.
        """
        if cls.client is not None:
            return

        logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI)
        try:
            # Add server selection timeout to get faster errors
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI, serverSelectionTimeoutMS=5000
            )
            # Test connection
            await cls.client.admin.command("ping")
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            logger.info("Connected to MongoDB database: %s", settings.MONGODB_DB_NAME)
        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", str(e))
            if hasattr(e, "details"):
                logger.error("Error details: %s", e.details)
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """
        Disconnect from MongoDB.

        This method closes the connection to MongoDB.
        """
        if cls.client is None:
            return

        logger.info("Disconnecting from MongoDB...")
        cls.client.close()
        cls.client = None
        cls.db = None
        logger.info("Disconnected from MongoDB")

    @classmethod
    def get_collection(cls, collection_name: str):
        """
        Get a MongoDB collection.

        Args:
            collection_name: The name of the collection.

        Returns:
            The MongoDB collection.
        """
        connection_error_msg = "MongoDB connection not established"
        if cls.db is None:
            raise RuntimeError(connection_error_msg)

        return cls.db[collection_name]


# Collection names
COLLECTION_CODE_ANALYSIS = "code_analysis"
