"""
Combined tests for the Animal API with proper async mocking
"""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
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

        with patch("main.aiohttp.ClientSession") as mock_session:
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
        with patch("main.aiohttp.ClientSession") as mock_session:
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
        with patch("main.aiohttp.ClientSession") as mock_session:
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

    def test_process_all_animals_no_animals(self, client):
        """Test processing when no animals found"""
        with patch("main.get_all_animal_ids") as mock_get_ids:
            mock_get_ids.return_value = []

            response = client.post("/process-all-animals")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "No animals found"
            assert data["total_animals"] == 0


class TestUtilityFunctions:
    """Tests for utility functions from utils.py"""

    def test_transform_animal_with_friends_string(self):
        """Test transformation with friends as a comma-separated string"""
        from utils import transform_animal

        animal = {
            "id": 1,
            "name": "Fluffy",
            "friends": "Buddy, Max, Luna",
            "born_at": 1640995200000,
        }

        result = transform_animal(animal)

        assert result["friends"] == ["Buddy", "Max", "Luna"]
        assert result["born_at"] == "2022-01-01T00:00:00Z"

    def test_transform_animal_with_empty_friends(self):
        """Test transformation with empty friends"""
        from utils import transform_animal

        animal = {"id": 1, "name": "Fluffy", "friends": ""}

        result = transform_animal(animal)

        assert result["friends"] == []

    def test_transform_animal_without_friends(self):
        """Test transformation without friends field"""
        from utils import transform_animal

        animal = {"id": 1, "name": "Fluffy"}

        result = transform_animal(animal)

        assert result["friends"] == []

    def test_transform_animal_with_string_date(self):
        """Test transformation with string date"""
        from utils import transform_animal

        animal = {"id": 1, "name": "Fluffy", "born_at": "2022-01-01"}

        result = transform_animal(animal)

        assert result["born_at"] == "2022-01-01T00:00:00Z"

    def test_transform_animal_with_invalid_date(self):
        """Test transformation with invalid date"""
        from utils import transform_animal

        animal = {"id": 1, "name": "Fluffy", "born_at": "invalid-date"}

        result = transform_animal(animal)

        assert result["born_at"] is None

    def test_transform_animal_with_none_born_at(self):
        """Test transformation with None born_at"""
        from utils import transform_animal

        animal = {"id": 1, "name": "Fluffy", "born_at": None}

        result = transform_animal(animal)

        assert result["born_at"] is None

    @pytest.mark.asyncio
    async def test_fetch_with_retry_successful(self):
        """Test successful fetch of data"""
        from utils import fetch_with_retry

        url = "http://test/api/data"
        mock_data = {"key": "value"}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                result = await fetch_with_retry(session, url)

            assert result == mock_data

    @pytest.mark.asyncio
    async def test_fetch_with_retry_not_found(self):
        """Test fetch returns None for 404 error"""
        from utils import fetch_with_retry

        url = "http://test/api/data"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                result = await fetch_with_retry(session, url)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_all_animal_ids_success(self):
        """Test successful retrieval of all animal IDs"""
        from utils import get_all_animal_ids

        base_url = "http://test"
        mock_data_page_1 = {"items": [{"id": 1}, {"id": 2}], "page": 1}

        # Empty list to end pagination
        mock_data_page_2 = {"items": [], "page": 2}

        with patch("utils.fetch_with_retry") as fetch_mock:
            # Simulate fetching two pages
            fetch_mock.side_effect = [mock_data_page_1, mock_data_page_2]

            result = await get_all_animal_ids(base_url)

            assert result == [1, 2]

    def test_chunk_list_even_chunks(self):
        """Test splitting list into even chunks"""
        from utils import chunk_list

        items = [0, 1, 2, 3, 4, 5]
        result = chunk_list(items, 2)

        assert result == [[0, 1], [2, 3], [4, 5]]

    def test_chunk_list_with_remainder(self):
        """Test splitting list with remainder"""
        from utils import chunk_list

        items = [0, 1, 2, 3, 4]
        result = chunk_list(items, 2)

        assert result == [[0, 1], [2, 3], [4]]

    def test_chunk_list_single_chunk(self):
        """Test entire list as a single chunk"""
        from utils import chunk_list

        items = [0, 1]
        result = chunk_list(items, 5)

        assert result == [[0, 1]]

    def test_chunk_list_empty_list(self):
        """Test chunking an empty list"""
        from utils import chunk_list

        items = []
        result = chunk_list(items, 3)

        assert result == []
