"""
Integration tests for full ETL workflow.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.animal_service import (
    fetch_and_transform_animals_with_session,
    process_all_animals_batch,
    process_batch_etl,
)


class TestFullETLWorkflow:
    """Integration tests for the complete ETL workflow"""

    @pytest.mark.asyncio
    async def test_process_batch_etl_success(self):
        """Test processing a single ETL batch successfully"""
        base_url = "http://localhost:3123"
        animal_ids = [1, 2, 3]
        batch_number = 1

        # Mock the session and its methods
        mock_session = MagicMock()

        # Mock the fetch_and_transform_animals_with_session
        mock_transformed_animals = [
            {"id": 1, "name": "Fluffy", "type": "cat"},
            {"id": 2, "name": "Buddy", "type": "dog"},
            {"id": 3, "name": "Whiskers", "type": "cat"},
        ]

        with patch(
            "app.services.animal_service.fetch_and_transform_animals_with_session"
        ) as mock_fetch_transform:
            with patch(
                "app.services.animal_service.post_batch_with_retry"
            ) as mock_post_batch:
                mock_fetch_transform.return_value = mock_transformed_animals
                mock_post_batch.return_value = True

                result = await process_batch_etl(
                    base_url, animal_ids, batch_number, mock_session
                )

                assert result["batch_number"] == 1
                assert result["processed"] == 3
                assert result["failed"] == 0
                assert result["success"] is True

                # Verify calls were made
                mock_fetch_transform.assert_called_once_with(
                    mock_session, base_url, animal_ids, max_concurrent=10
                )
                mock_post_batch.assert_called_once_with(
                    mock_session, base_url, mock_transformed_animals
                )

    @pytest.mark.asyncio
    async def test_process_batch_etl_transform_failure(self):
        """Test processing batch when transformation fails"""
        base_url = "http://localhost:3123"
        animal_ids = [1, 2, 3]
        batch_number = 1

        mock_session = MagicMock()

        with patch(
            "app.services.animal_service.fetch_and_transform_animals_with_session"
        ) as mock_fetch_transform:
            # Mock no transformed animals (all failed)
            mock_fetch_transform.return_value = []

            result = await process_batch_etl(
                base_url, animal_ids, batch_number, mock_session
            )

            assert result["batch_number"] == 1
            assert result["processed"] == 0
            assert result["failed"] == 3
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_process_batch_etl_post_failure(self):
        """Test processing batch when posting fails"""
        base_url = "http://localhost:3123"
        animal_ids = [1, 2, 3]
        batch_number = 1

        mock_session = MagicMock()
        mock_transformed_animals = [
            {"id": 1, "name": "Fluffy", "type": "cat"},
        ]

        with patch(
            "app.services.animal_service.fetch_and_transform_animals_with_session"
        ) as mock_fetch_transform:
            with patch(
                "app.services.animal_service.post_batch_with_retry"
            ) as mock_post_batch:
                mock_fetch_transform.return_value = mock_transformed_animals
                mock_post_batch.return_value = False  # Post failed

                result = await process_batch_etl(
                    base_url, animal_ids, batch_number, mock_session
                )

                assert result["batch_number"] == 1
                assert result["processed"] == 0
                assert result["failed"] == 3
                assert result["success"] is False

    @pytest.mark.asyncio
    async def test_fetch_and_transform_animals_with_session(self):
        """Test fetching and transforming animals with session"""
        base_url = "http://localhost:3123"
        animal_ids = [1, 2]

        # Mock session and responses
        mock_session = MagicMock()

        # Mock animal data responses
        mock_animal_1 = {"id": 1, "name": "Fluffy", "type": "cat", "friends": "Buddy"}
        mock_animal_2 = {"id": 2, "name": "Buddy", "type": "dog", "friends": ""}

        with patch("app.services.animal_service.fetch_with_retry") as mock_fetch:
            with patch(
                "app.services.animal_service.transform_animal"
            ) as mock_transform:
                # Setup fetch responses
                mock_fetch.side_effect = [mock_animal_1, mock_animal_2]

                # Setup transform responses
                mock_transform.side_effect = [
                    {"id": 1, "name": "Fluffy", "type": "cat", "friends": ["Buddy"]},
                    {"id": 2, "name": "Buddy", "type": "dog", "friends": []},
                ]

                result = await fetch_and_transform_animals_with_session(
                    mock_session, base_url, animal_ids, max_concurrent=2
                )

                assert len(result) == 2
                assert result[0]["id"] == 1
                assert result[1]["id"] == 2
                assert result[0]["friends"] == ["Buddy"]
                assert result[1]["friends"] == []

                # Verify correct number of calls
                assert mock_fetch.call_count == 2
                assert mock_transform.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_and_transform_animals_with_failures(self):
        """Test fetching animals with some failures"""
        base_url = "http://localhost:3123"
        animal_ids = [1, 2, 3]

        mock_session = MagicMock()

        with patch("app.services.animal_service.fetch_with_retry") as mock_fetch:
            with patch(
                "app.services.animal_service.transform_animal"
            ) as mock_transform:
                # Setup fetch responses - one success, one failure, one success
                mock_animal_1 = {"id": 1, "name": "Fluffy", "type": "cat"}
                mock_animal_3 = {"id": 3, "name": "Whiskers", "type": "cat"}

                mock_fetch.side_effect = [mock_animal_1, None, mock_animal_3]

                # Setup transform responses for successful fetches
                mock_transform.side_effect = [
                    {"id": 1, "name": "Fluffy", "type": "cat"},
                    {"id": 3, "name": "Whiskers", "type": "cat"},
                ]

                result = await fetch_and_transform_animals_with_session(
                    mock_session, base_url, animal_ids, max_concurrent=3
                )

                # Should only get 2 successful transformations
                assert len(result) == 2
                assert result[0]["id"] == 1
                assert result[1]["id"] == 3

                # Verify calls
                assert mock_fetch.call_count == 3
                assert mock_transform.call_count == 2


class TestETLConcurrencyAndParallelism:
    """Tests for concurrency and parallelism in ETL processing"""

    @pytest.mark.asyncio
    async def test_concurrent_batch_processing_simulation(self):
        """Test that multiple batches can be processed with proper
        concurrency control"""

        # This test simulates concurrent processing behavior
        base_url = "http://localhost:3123"

        # Mock data for multiple batches
        batch_data = [
            ([1, 2, 3], 1),  # (animal_ids, batch_number)
            ([4, 5, 6], 2),
            ([7, 8, 9], 3),
        ]

        results = []

        with patch("app.services.animal_service.fetch_with_retry") as mock_fetch:
            with patch(
                "app.services.animal_service.post_batch_with_retry"
            ) as mock_post:
                with patch(
                    "app.services.animal_service.transform_animal"
                ) as mock_transform:
                    # Setup successful responses
                    mock_fetch.return_value = {"id": 1, "name": "Test", "type": "cat"}
                    mock_transform.return_value = {
                        "id": 1,
                        "name": "Test",
                        "type": "cat",
                    }
                    mock_post.return_value = True

                    # Create tasks for concurrent processing (simulated)
                    tasks = []
                    for animal_ids, batch_number in batch_data:
                        mock_session = MagicMock()
                        task = process_batch_etl(
                            base_url, animal_ids, batch_number, mock_session
                        )
                        tasks.append(task)

                    # Execute tasks concurrently
                    results = await asyncio.gather(*tasks)

                    # Verify all batches were processed
                    assert len(results) == 3
                    for i, result in enumerate(results):
                        assert result["batch_number"] == i + 1
                        assert result["success"] is True
                        assert result["processed"] == 3

    @pytest.mark.asyncio
    async def test_semaphore_concurrency_control(self):
        """Test that semaphore properly controls concurrent requests"""

        base_url = "http://localhost:3123"
        animal_ids = list(range(1, 21))  # 20 animals
        mock_session = MagicMock()

        call_times = []

        async def mock_fetch_with_delay(*args, **kwargs):
            """Mock fetch that records call times"""
            import time

            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"id": args[1].split("/")[-1], "name": "Test", "type": "cat"}

        with patch(
            "app.services.animal_service.fetch_with_retry",
            side_effect=mock_fetch_with_delay,
        ):
            with patch(
                "app.services.animal_service.transform_animal"
            ) as mock_transform:
                mock_transform.return_value = {"id": 1, "name": "Test", "type": "cat"}

                start_time = asyncio.get_event_loop().time()

                result = await fetch_and_transform_animals_with_session(
                    mock_session, base_url, animal_ids, max_concurrent=5
                )

                end_time = asyncio.get_event_loop().time()

                # Verify results
                assert len(result) == 20

                # With max_concurrent=5 and 20 items, we should have ~4 batches
                # Total time should be roughly 4 * 0.1 = 0.4 seconds (plus overhead)
                execution_time = end_time - start_time
                assert (
                    execution_time < 1.0
                )  # Should be much faster than sequential (2.0s)
                assert execution_time > 0.3  # But not instantaneous
