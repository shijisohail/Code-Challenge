"""
Unit tests for health endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["service"] == "Animal API"

    def test_health_check_structure(self, client):
        """Test health check response structure"""
        response = client.get("/health")
        data = response.json()

        # Verify all required fields are present
        required_fields = ["status", "timestamp", "version", "service"]
        for field in required_fields:
            assert field in data

        # Verify types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["service"], str)
