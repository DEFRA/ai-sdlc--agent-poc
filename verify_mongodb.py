#!/usr/bin/env python3
"""
MongoDB Connection Verification Script.

This script verifies the connection to MongoDB using the configured settings.
It can be used to troubleshoot authentication issues.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ai-sdlc--agent-poc")


async def verify_connection():
    """Verify connection to MongoDB."""
    logger.info("Verifying connection to MongoDB at: %s", MONGODB_URI)
    logger.info("Using database: %s", MONGODB_DB_NAME)

    try:
        # Connect to MongoDB with a timeout
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

        # Verify connection by issuing a ping command
        await client.admin.command("ping")
        logger.info("✅ Successfully connected to MongoDB")

        # Verify database access
        db = client[MONGODB_DB_NAME]
        collections = await db.list_collection_names()
        logger.info("✅ Successfully accessed database. Collections: %s", collections)

        # Try to access the code_analysis collection
        if "code_analysis" in collections:
            count = await db.code_analysis.count_documents({})
            logger.info(
                "✅ Successfully accessed code_analysis collection. Document count: %s",
                count,
            )
        else:
            logger.warning(
                "❌ code_analysis collection not found. You may need to run mongo_init.py"
            )

        return True
    except ConnectionFailure as e:
        logger.error("❌ Could not connect to MongoDB: %s", e)
        return False
    except ServerSelectionTimeoutError as e:
        logger.error("❌ Server selection timeout: %s", e)
        logger.error("This usually means the server is not running or not accessible")
        return False
    except Exception as e:
        logger.error("❌ Error verifying MongoDB connection: %s", e)
        if hasattr(e, "details"):
            logger.error("Error details: %s", e.details)
        return False
    finally:
        # Close the connection
        if "client" in locals():
            client.close()


async def print_connection_info():
    """Print information about the MongoDB connection settings."""
    logger.info("MongoDB Connection Information:")
    logger.info("- MONGODB_URI: %s", MONGODB_URI)
    logger.info("- MONGODB_DB_NAME: %s", MONGODB_DB_NAME)

    # Parse connection string for more details
    if MONGODB_URI.startswith("mongodb://"):
        # Remove mongodb:// prefix
        connection_info = MONGODB_URI[10:]

        # Split auth and host info
        if "@" in connection_info:
            auth_info, host_info = connection_info.split("@", 1)

            # Extract username and password
            if ":" in auth_info:
                username, password = auth_info.split(":", 1)
                masked_password = "*" * len(password)
                logger.info("- Username: %s", username)
                logger.info("- Password: %s", masked_password)

            # Extract host and port
            if "/" in host_info:
                host_port, db = host_info.split("/", 1)
                logger.info("- Host: %s", host_port)
                logger.info("- Database in URI: %s", db)
            else:
                logger.info("- Host: %s", host_info)
        else:
            # No authentication in URI
            logger.info("- No authentication credentials in URI")


if __name__ == "__main__":
    logger.info("Starting MongoDB connection verification")

    asyncio.run(print_connection_info())
    success = asyncio.run(verify_connection())

    sys.exit(0 if success else 1)
