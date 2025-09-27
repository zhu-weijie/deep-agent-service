from fastapi import FastAPI
from .config import settings

# Instantiate the FastAPI application
app = FastAPI(
    title="Deep Agent Service",
    description="A FastAPI service for the Deep Agent research agent.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint to confirm the service is running
    and loading configuration correctly.
    """
    return {"status": "ok", "environment": settings.ENVIRONMENT}
