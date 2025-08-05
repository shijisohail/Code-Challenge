"""
Unit tests for ETL processing functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestETLProcessing:
    """Tests for ETL processing endpoint"""

    @patch("app.api.endpoints.process_all_animals_batch")
    def test_process_all_animals_success(self, mock_process, client):
        """Test successful ETL processing"""
        mock_process.return_value = {
            "message": "ETL processing complete",
            "total_animals": 50,
            "processed_animals": 45,
            "failed_animals": 5,
            "batches_sent": 2,
            "total_batches": 2,
        }

        response = client.post("/process-all-animals")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ETL processing complete"
        assert data["total_animals"] == 50
        assert data["processed_animals"] == 45
        assert data["failed_animals"] == 5
        assert data["batches_sent"] == 2

        # Verify the mock was called
        mock_process.assert_called_once()

    @patch("app.api.endpoints.process_all_animals_batch")
    def test_process_all_animals_no_animals(self, mock_process, client):
        """Test processing when no animals found using ETL approach"""
        mock_process.return_value = {
            "message": "ETL processing complete",
            "total_animals": 0,
            "processed_animals": 0,
            "failed_animals": 0,
            "batches_sent": 0,
            "total_batches": 0,
        }

        response = client.post("/process-all-animals")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ETL processing complete"
        assert data["total_animals"] == 0
        assert data["processed_animals"] == 0
        assert data["batches_sent"] == 0

        # Verify the mock was called
        mock_process.assert_called_once()

    @patch("app.api.endpoints.process_all_animals_batch")
    def test_process_all_animals_error(self, mock_process, client):
        """Test ETL processing with error"""
        mock_process.side_effect = Exception("Processing failed")

        response = client.post("/process-all-animals")
        assert response.status_code == 500
        assert "Processing failed" in response.json()["detail"]

        # Verify the mock was called
        mock_process.assert_called_once()

    @patch("app.api.endpoints.process_all_animals_batch")
    def test_process_all_animals_partial_failure(self, mock_process, client):
        """Test ETL processing with partial failures"""
        mock_process.return_value = {
            "message": "ETL processing complete",
            "total_animals": 100,
            "processed_animals": 85,
            "failed_animals": 15,
            "batches_sent": 4,
            "total_batches": 5,  # One batch failed
        }

        response = client.post("/process-all-animals")
        assert response.status_code == 200
        data = response.json()
        assert data["total_animals"] == 100
        assert data["processed_animals"] == 85
        assert data["failed_animals"] == 15
        assert data["batches_sent"] == 4
        assert data["total_batches"] == 5

    @patch("app.api.endpoints.process_all_animals_batch")
    def test_process_all_animals_large_dataset(self, mock_process, client):
        """Test ETL processing with large dataset"""
        mock_process.return_value = {
            "message": "ETL processing complete",
            "total_animals": 1000,
            "processed_animals": 995,
            "failed_animals": 5,
            "batches_sent": 10,
            "total_batches": 10,
        }

        response = client.post("/process-all-animals")
        assert response.status_code == 200
        data = response.json()
        assert data["total_animals"] == 1000
        assert data["processed_animals"] == 995
        assert data["failed_animals"] == 5
        assert data["batches_sent"] == 10
