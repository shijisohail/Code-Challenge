"""
Tests for service layer utilities.
"""

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from app.services.data_transformer import chunk_list, transform_animal
from app.services.http_client import fetch_with_retry


class TestDataTransformer:
    """Tests for data transformation functions"""

    def test_transform_animal_with_friends_string(self):
        """Test transformation with friends as a comma-separated string"""
        animal = {
            "id": 1,
            "name": "Fluffy",
            "friends": "Buddy, Max, Luna",
            "born_at": 1640995200000,
        }

        result = transform_animal(animal)

        assert result["friends"] == ["Buddy", "Max", "Luna"]
        assert result["born_at"] == "2022-01-01T00:00:00+00:00"

    def test_transform_animal_with_empty_friends(self):
        """Test transformation with empty friends"""
        animal = {"id": 1, "name": "Fluffy", "friends": ""}

        result = transform_animal(animal)

        assert result["friends"] == []

    def test_transform_animal_without_friends(self):
        """Test transformation without friends field"""
        animal = {"id": 1, "name": "Fluffy"}

        result = transform_animal(animal)

        assert result["friends"] == []

    def test_transform_animal_with_string_date(self):
        """Test transformation with string date"""
        animal = {"id": 1, "name": "Fluffy", "born_at": "2022-01-01"}

        result = transform_animal(animal)

        assert result["born_at"] == "2022-01-01T00:00:00+00:00"

    def test_transform_animal_with_invalid_date(self):
        """Test transformation with invalid date"""
        animal = {"id": 1, "name": "Fluffy", "born_at": "invalid-date"}

        result = transform_animal(animal)

        assert result["born_at"] == "invalid-date"

    def test_transform_animal_with_none_born_at(self):
        """Test transformation with None born_at"""
        animal = {"id": 1, "name": "Fluffy", "born_at": None}

        result = transform_animal(animal)

        assert result["born_at"] is None

    def test_chunk_list_even_chunks(self):
        """Test splitting list into even chunks"""
        items = [0, 1, 2, 3, 4, 5]
        result = chunk_list(items, 2)

        assert result == [[0, 1], [2, 3], [4, 5]]

    def test_chunk_list_with_remainder(self):
        """Test splitting list with remainder"""
        items = [0, 1, 2, 3, 4]
        result = chunk_list(items, 2)

        assert result == [[0, 1], [2, 3], [4]]

    def test_chunk_list_single_chunk(self):
        """Test entire list as a single chunk"""
        items = [0, 1]
        result = chunk_list(items, 5)

        assert result == [[0, 1]]

    def test_chunk_list_empty_list(self):
        """Test chunking an empty list"""
        items = []
        result = chunk_list(items, 3)

        assert result == []


class TestHTTPClient:
    """Tests for HTTP client functions"""

    @pytest.mark.asyncio
    async def test_fetch_with_retry_successful(self):
        """Test successful fetch of data"""
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
        url = "http://test/api/data"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                result = await fetch_with_retry(session, url)

            assert result is None
