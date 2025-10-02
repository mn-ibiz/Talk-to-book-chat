"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
import os

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"


@pytest.fixture
def client():
    """Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client instance
    """
    from src.main import app
    return TestClient(app)


@pytest.fixture
def sample_messages():
    """Provide sample message data for testing.

    Returns:
        list: Sample messages in the expected format
    """
    return [
        {"role": "user", "content": "Hello, I want to write a book"}
    ]
