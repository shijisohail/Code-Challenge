"""
Unit tests for animal endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestReceiveAnimalsEndpoint:
    """Tests for receive animals endpoint"""

    def test_receive_animals_success(self, client):
        """Test successful receipt of animals"""
        animals_data = [
            {"id": 1, "name": "Fluffy", "type": "cat"},
            {"id": 2, "name": "Buddy", "type": "dog"},
        ]

        response = client.post("/animals/v1/home", json=animals_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully received 2 animals"
        assert data["count"] == 2

    def test_receive_animals_empty_list(self, client):
        """Test receiving empty animals list"""
        response = client.post("/animals/v1/home", json=[])
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_receive_animals_too_many(self, client):
        """Test receiving too many animals (>100)"""
        animals_data = [{"id": i, "name": f"Animal{i}"} for i in range(101)]
        response = client.post("/animals/v1/home", json=animals_data)
        assert response.status_code == 400
        assert "Maximum 100 animals per batch" in response.json()["detail"]

    def test_receive_animals_invalid_data(self, client):
        """Test receiving invalid animals data"""
        response = client.post("/animals/v1/home", json="invalid")
        assert response.status_code == 422  # FastAPI validation error

    def test_receive_animals_single_animal(self, client):
        """Test receiving single animal"""
        animal_data = [{"id": 1, "name": "Rex", "type": "dog"}]
        response = client.post("/animals/v1/home", json=animal_data)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_receive_animals_maximum_allowed(self, client):
        """Test receiving exactly 100 animals (boundary test)"""
        animals_data = [{"id": i, "name": f"Animal{i}"} for i in range(100)]
        response = client.post("/animals/v1/home", json=animals_data)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 100


class TestExternalAPIEndpoints:
    """Tests for endpoints that call external APIs"""

    def test_get_animals_success(self, client):
        """Test successful retrieval of animals"""
        mock_data = {
            "items": [
                {"id": 1, "name": "Fluffy", "type": "cat"},
                {"id": 2, "name": "Buddy", "type": "dog"},
            ],
            "page": 1,
            "total": 2,
        }

        with patch("app.api.endpoints.aiohttp.ClientSession") as mock_session:
            # Create mock response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_data)

            # Create mock context manager for the get request
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_response

            # Create mock session context manager
            mock_session_instance = MagicMock()
            mock_session_instance.get.return_value = mock_context

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_context

            response = client.get("/animals")
            assert response.status_code == 200
            assert response.json() == mock_data

    def test_get_animals_api_error(self, client):
        """Test animals endpoint when external API returns error"""
        with patch("app.api.endpoints.aiohttp.ClientSession") as mock_session:
            # Create mock response with error status
            mock_response = MagicMock()
            mock_response.status = 500

            # Create mock context manager for the get request
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_response

            # Create mock session context manager
            mock_session_instance = MagicMock()
            mock_session_instance.get.return_value = mock_context

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_context

            response = client.get("/animals")
            assert response.status_code == 500
            assert "Failed to fetch animals" in response.json()["detail"]

    def test_get_animal_details_not_found(self, client):
        """Test animal details endpoint when animal not found"""
        with patch("app.api.endpoints.aiohttp.ClientSession") as mock_session:
            # Create mock response with 404 status
            mock_response = MagicMock()
            mock_response.status = 404

            # Create mock context manager for the get request
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_response

            # Create mock session context manager
            mock_session_instance = MagicMock()
            mock_session_instance.get.return_value = mock_context

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_context

            response = client.get("/animals/999")
            assert response.status_code == 404
            assert "Animal with ID 999 not found" in response.json()["detail"]

    def test_get_animals_with_page_parameter(self, client):
        """Test animals endpoint with page parameter"""
        mock_data = {
            "items": [{"id": 3, "name": "Whiskers", "type": "cat"}],
            "page": 2,
            "total": 1,
        }

        with patch("app.api.endpoints.aiohttp.ClientSession") as mock_session:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_data)

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_response

            mock_session_instance = MagicMock()
            mock_session_instance.get.return_value = mock_context

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_context

            response = client.get("/animals?page=2")
            assert response.status_code == 200
            assert response.json() == mock_data
