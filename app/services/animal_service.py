"""
Animal service containing business logic for animal operations.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from ..core.config import config
from .data_transformer import chunk_list, transform_animal
from .http_client import fetch_with_retry, post_batch_with_retry

logger = logging.getLogger(__name__)


async def get_all_animal_ids(base_url: str) -> List[int]:
    """Fetch all animal IDs from paginated API."""
    animal_ids = []
    page = 1

    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{base_url}/animals/v1/animals?page={page}"
            logger.info(f"Fetching animals page {page}")

            data = await fetch_with_retry(session, url)
            if not data or "items" not in data or not data["items"]:
                break

            page_ids = [animal["id"] for animal in data["items"]]
            animal_ids.extend(page_ids)
            logger.info(f"Found {len(page_ids)} animals on page {page}")
            page += 1

    logger.info(f"Total animals found: {len(animal_ids)}")
    return animal_ids


async def fetch_and_transform_animals(
    base_url: str, animal_ids: List[int], max_concurrent: int = None
) -> List[Dict[str, Any]]:
    """Fetch and transform animals concurrently."""
    if max_concurrent is None:
        max_concurrent = config.MAX_CONCURRENT_REQUESTS

    semaphore = asyncio.Semaphore(max_concurrent)
    transformed_animals = []
    failed_animals = []

    async def fetch_single_animal(animal_id: int) -> Optional[Dict[str, Any]]:
        async with semaphore:  # Limit concurrent requests
            url = f"{base_url}/animals/v1/animals/{animal_id}"
            animal_data = await fetch_with_retry(session, url)

            if animal_data:
                return transform_animal(animal_data)
            logger.warning(f"Failed to fetch animal {animal_id} after all retries")
            return None

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=50, limit_per_host=20)
    ) as session:
        # Process animals in batches to avoid overwhelming the server
        batch_size = 50

        for i in range(0, len(animal_ids), batch_size):
            batch_ids = animal_ids[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1}: "
                f"animals {i + 1}-{min(i + batch_size, len(animal_ids))}"
            )

            # Create tasks for this batch
            tasks = [fetch_single_animal(animal_id) for animal_id in batch_ids]

            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for animal_id, result in zip(batch_ids, results):
                if isinstance(result, Exception):
                    logger.error(f"Exception fetching animal {animal_id}: {result}")
                    failed_animals.append(animal_id)
                elif result is not None and isinstance(result, dict):
                    transformed_animals.append(result)
                else:
                    failed_animals.append(animal_id)

            # Small delay between batches to be server-friendly
            if i + batch_size < len(animal_ids):
                await asyncio.sleep(0.5)

    success_count = len(transformed_animals)
    failure_count = len(failed_animals)

    logger.info(
        f"Animal processing complete: {success_count} successful, "
        f"{failure_count} failed"
    )

    if failed_animals:
        logger.warning(
            f"Failed animal IDs: {failed_animals[:10]}"
            f"{'...' if len(failed_animals) > 10 else ''}"
        )

    return transformed_animals


async def process_all_animals_batch(base_url: str) -> Dict[str, Any]:
    """Process all animals and send them in batches."""
    logger.info("Starting to process all animals")

    animal_ids = await get_all_animal_ids(base_url)
    if not animal_ids:
        return {
            "message": "No animals found",
            "total_animals": 0,
            "batches_sent": 0,
            "failed_animals": 0,
        }

    transformed_animals = await fetch_and_transform_animals(base_url, animal_ids)

    batches = chunk_list(transformed_animals, config.MAX_ANIMALS_PER_BATCH)
    batches_sent = 0
    failed_animals = len(animal_ids) - len(transformed_animals)

    async with aiohttp.ClientSession() as session:
        for batch in batches:
            success = await post_batch_with_retry(session, base_url, batch)
            if success:
                batches_sent += 1
            else:
                failed_animals += len(batch)

    return {
        "message": "Processing complete",
        "total_animals": len(animal_ids),
        "batches_sent": batches_sent,
        "failed_animals": failed_animals,
    }
