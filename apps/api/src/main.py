"""Talk2Publish API - Main application entry point."""

# Load environment variables FIRST (before any other imports)
from dotenv import load_dotenv
from pathlib import Path

# Calculate project root and load .env
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Talk2Publish API",
    description="AI-powered ghostwriting partner for authors",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment validation.

    Returns:
        dict: Status information
    """
    logger.info("Health check requested")
    return {
        "status": "ok",
        "service": "talk2publish-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information.

    Returns:
        dict: API welcome message
    """
    return {
        "message": "Talk2Publish API",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
