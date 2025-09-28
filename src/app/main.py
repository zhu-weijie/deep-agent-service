import logging
from fastapi import FastAPI

from .config import settings
from .api.routes import router as api_router
from .logging_config import setup_logging

# Get the logger instance
logger = logging.getLogger(__name__)

# Call the setup function to configure logging
setup_logging()

# Instantiate the FastAPI application
app = FastAPI(
    title="Deep Agent Service",
    description="A FastAPI service for the Deep Agent research agent.",
    version="0.1.0",
)

# Include the API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint to confirm the service is running
    and loading configuration correctly.
    """
    logger.info("Health check endpoint was called.")
    return {"status": "ok", "environment": settings.ENVIRONMENT}
