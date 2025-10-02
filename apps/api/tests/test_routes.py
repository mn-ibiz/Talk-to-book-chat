"""Tests for API routes."""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_returns_correct_structure(self, client):
        """Test that health check returns expected JSON structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data

    def test_health_check_status_is_ok(self, client):
        """Test that health check status is 'ok'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "ok"
        assert data["service"] == "talk2publish-api"


class TestRootEndpoint:
    """Test suite for the / root endpoint."""

    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_root_returns_api_info(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestChatEndpoint:
    """Test suite for the /chat endpoint."""

    def test_chat_endpoint_exists(self, client):
        """Test that chat endpoint is accessible."""
        response = client.post(
            "/chat/",
            json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        # Should not return 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_chat_requires_messages(self, client):
        """Test that chat endpoint requires messages field."""
        response = client.post("/chat/", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY to be configured")
    def test_chat_returns_response(self, client, sample_messages):
        """Test that chat endpoint returns a response.

        Note: This test is skipped by default as it requires a valid
        ANTHROPIC_API_KEY to be configured.
        """
        response = client.post(
            "/chat/",
            json={"messages": sample_messages}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "messages" in data
        assert "thread_id" in data
        assert isinstance(data["messages"], list)
