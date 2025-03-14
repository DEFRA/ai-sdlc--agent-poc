"""Main application module."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.api.v1.code_analysis import router as code_analysis_router
from src.config.settings import settings
from src.database.mongodb import MongoDB

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    FastAPI lifespan event handler.

    This function is called when the application starts and stops.
    It is used to connect to MongoDB when the application starts
    and disconnect when the application stops.
    """
    # On startup
    logger.info("Starting up...")
    try:
        await MongoDB.connect()
    except Exception as e:
        logger.error("Failed to initialize application: %s", e)
        raise

    yield

    # On shutdown
    logger.info("Shutting down...")
    await MongoDB.disconnect()


app = FastAPI(
    title="Code Analysis API",
    description="API for analyzing code repositories and generating architecture documentation",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
api_v1_router.include_router(code_analysis_router)
app.include_router(api_v1_router)


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
