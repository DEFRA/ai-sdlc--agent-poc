#!/usr/bin/env python3
"""
MongoDB Initialization Script.

This script initializes the MongoDB database for the code analysis API.
It creates the necessary user, collection, and indexes.
"""

import logging
import os
import sys

import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient
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
DB_NAME = os.getenv("MONGODB_DB_NAME", "ai-sdlc--agent-poc")
COLLECTION_NAME = "code_analysis"
USERNAME = "code_analysis_user"
# Note: This is a hardcoded password for the MongoDB init script only
PASSWORD = "code_analysis_password"  # noqa: S105 - Acceptable for initialization script
ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27018"))


def create_user(client):
    """
    Create a database user with appropriate permissions.

    Args:
        client: MongoDB client with admin access
    """
    try:
        # Check if user already exists - using a different approach
        try:
            # Try to authenticate with the user
            test_uri = (
                f"mongodb://{USERNAME}:{PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}"
            )
            test_client = MongoClient(test_uri, serverSelectionTimeoutMS=2000)
            test_client.admin.command("ping")
            logger.info("User %s already exists and can authenticate", USERNAME)
            return
        except Exception as e:
            # User doesn't exist or can't authenticate, which is expected
            logger.debug("User authentication failed as expected: %s", e)

        # Create user with the admin database
        logger.info("Creating user %s in database %s", USERNAME, DB_NAME)

        # Use the simpler approach - create user directly in the target database
        db = client[DB_NAME]
        db.command("createUser", USERNAME, pwd=PASSWORD, roles=["readWrite"])

        logger.info("Created user %s with readWrite access to %s", USERNAME, DB_NAME)
    except Exception as e:
        logger.error("Error creating user: %s", e)
        raise


def create_collection_with_validation(client):
    """
    Create the code_analysis collection with JSON schema validation.

    Args:
        client: MongoDB client with database access
    """
    try:
        db = client[DB_NAME]

        # Check if collection already exists
        if COLLECTION_NAME in db.list_collection_names():
            logger.info("Collection %s already exists", COLLECTION_NAME)
            return

        # Define the validation schema
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["repository_url", "status", "created_at", "updated_at"],
                "properties": {
                    "repository_url": {
                        "bsonType": "string",
                        "description": "URL of the repository to analyze",
                    },
                    "status": {
                        "enum": ["IN_PROGRESS", "COMPLETED", "ERROR"],
                        "description": "Current status of the analysis",
                    },
                    "architecture_documentation": {
                        "bsonType": ["string", "null"],
                        "description": "Architecture documentation in markdown or structured format",
                    },
                    "ingested_repository": {
                        "bsonType": ["string", "null"],
                        "description": "The ingested repository data",
                    },
                    "technologies": {
                        "bsonType": ["array", "null"],
                        "description": "List of technologies used in the repository",
                        "items": {"bsonType": "string"},
                    },
                    "data_model_files": {
                        "bsonType": ["array", "null"],
                        "description": "List of identified data model files",
                        "items": {"bsonType": "string"},
                    },
                    "data_model_analysis": {
                        "bsonType": ["string", "null"],
                        "description": "Generated data model analysis with ERD",
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Timestamp when the analysis was created",
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Timestamp when the analysis was last updated",
                    },
                },
            }
        }

        # Create the collection with validation
        db.create_collection(COLLECTION_NAME, validator=validator)

        logger.info("Created collection %s with validation rules", COLLECTION_NAME)
    except Exception as e:
        logger.error("Error creating collection: %s", e)
        raise


def create_indexes(client):
    """
    Create indexes for better query performance.

    Args:
        client: MongoDB client with database access
    """
    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Create indexes
        collection.create_index([("repository_url", pymongo.ASCENDING)])
        collection.create_index([("status", pymongo.ASCENDING)])
        collection.create_index([("created_at", pymongo.ASCENDING)])

        logger.info("Created indexes for collection %s", COLLECTION_NAME)
    except Exception as e:
        logger.error("Error creating indexes: %s", e)
        raise


def initialize_database():
    """Initialize the MongoDB database."""
    # Connect with admin credentials
    admin_uri = (
        f"mongodb://{ROOT_USERNAME}:{ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/admin"
    )

    try:
        # Connect to MongoDB
        client = MongoClient(admin_uri, serverSelectionTimeoutMS=5000)

        # Check if connection is successful
        client.admin.command("ismaster")
        logger.info("Successfully connected to MongoDB")

        # Create user, collection, and indexes
        create_user(client)
        create_collection_with_validation(client)
        create_indexes(client)

        logger.info("MongoDB initialization completed successfully")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error("Could not connect to MongoDB: %s", e)
        return False
    except Exception as e:
        logger.error("Error initializing MongoDB: %s", e)
        return False
    finally:
        # Close the connection
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    logger.info("Starting MongoDB initialization")
    success = initialize_database()
    sys.exit(0 if success else 1)
