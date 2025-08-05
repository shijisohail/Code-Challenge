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


async def fetch_and_transform_animals_with_session(
    session: aiohttp.ClientSession,
    base_url: str,
    animal_ids: List[int],
    max_concurrent: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Fetch and transform animals concurrently using provided session."""
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

    # Create tasks for all animals in this batch
    tasks = [fetch_single_animal(animal_id) for animal_id in animal_ids]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for animal_id, result in zip(animal_ids, results):
        if isinstance(result, Exception):
            logger.error(f"Exception fetching animal {animal_id}: {result}")
            failed_animals.append(animal_id)
        elif result is not None and isinstance(result, dict):
            transformed_animals.append(result)
        else:
            failed_animals.append(animal_id)

    success_count = len(transformed_animals)
    failure_count = len(failed_animals)

    logger.info(
        f"Batch processing complete: {success_count} successful, "
        f"{failure_count} failed"
    )

    if failed_animals:
        logger.warning(
            f"Failed animal IDs in batch: {failed_animals[:10]}"
            f"{'...' if len(failed_animals) > 10 else ''}"
        )

    return transformed_animals


async def fetch_and_transform_animals(
    base_url: str, animal_ids: List[int], max_concurrent: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetch and transform animals concurrently
    (legacy function for backward compatibility).
    """
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=50, limit_per_host=20)
    ) as session:
        return await fetch_and_transform_animals_with_session(
            session, base_url, animal_ids, max_concurrent
        )


async def process_batch_etl(
    base_url: str,
    animal_ids: List[int],
    batch_number: int,
    session: aiohttp.ClientSession,
) -> Dict[str, Any]:
    """Process a single batch following ETL principles: Extract -> Transform -> Load."""
    batch_size = len(animal_ids)
    logger.info(f"Processing ETL batch {batch_number}: {batch_size} animals")

    # TRANSFORM: Fetch and transform this batch of animals in parallel
    transformed_animals = await fetch_and_transform_animals_with_session(
        session, base_url, animal_ids, max_concurrent=config.MAX_CONCURRENT_REQUESTS
    )

    # LOAD: Post the transformed batch
    if transformed_animals:
        success = await post_batch_with_retry(session, base_url, transformed_animals)
        if success:
            logger.info(
                f"Successfully processed ETL batch {batch_number}: "
                f"{len(transformed_animals)} animals"
            )
            return {
                "batch_number": batch_number,
                "processed": len(transformed_animals),
                "failed": batch_size - len(transformed_animals),
                "success": True,
            }
        else:
            logger.error(f"Failed to post ETL batch {batch_number}")
            return {
                "batch_number": batch_number,
                "processed": 0,
                "failed": batch_size,
                "success": False,
            }
    else:
        logger.warning(f"No animals transformed in ETL batch {batch_number}")
        return {
            "batch_number": batch_number,
            "processed": 0,
            "failed": batch_size,
            "success": False,
        }


import asyncio
from concurrent.futures import ThreadPoolExecutor


async def process_all_animals_batch(base_url: str) -> Dict[str, Any]:
    """Process all animals following ETL principles:
    Extract batches - Transform - Load - repeat.
    Parallelize processing using concurrent tasks.
    """
    logger.info("Starting ETL processing of all animals")

    total_animals = 0
    total_processed = 0
    total_failed = 0
    batches_sent = 0
    batch_number = 1

    async with aiohttp.ClientSession() as session:
        page = 1

        while True:
            # EXTRACT: Get next batch of animal IDs (up to MAX_ANIMALS_PER_BATCH)
            logger.info(f"Extracting animals from page {page}")

            url = f"{base_url}/animals/v1/animals?page={page}"
            data = await fetch_with_retry(session, url)

            if not data or "items" not in data or not data["items"]:
                logger.info(
                    f"No more animals found on page {page}. ETL processing complete."
                )
                break

            page_animal_ids = [animal["id"] for animal in data["items"]]
            total_animals += len(page_animal_ids)

            logger.info(f"Extracted {len(page_animal_ids)} animal IDs from page {page}")

            # Process page data in ETL batches of MAX_ANIMALS_PER_BATCH
            batches = chunk_list(page_animal_ids, config.MAX_ANIMALS_PER_BATCH)

            # Create concurrent tasks for batch processing
            tasks = [
                process_batch_etl(base_url, batch_ids, batch_number + i, session)
                for i, batch_ids in enumerate(batches)
            ]

            # Execute all batch processing tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Exception in batch processing: {result}")
                    total_failed += (
                        config.MAX_ANIMALS_PER_BATCH
                    )  # Assume full batch failed
                else:
                    total_processed += result["processed"]
                    total_failed += result["failed"]

                    if result["success"]:
                        batches_sent += 1

            batch_number += len(batches)
            page += 1

    logger.info(
        f"ETL processing complete: {total_processed} processed, "
        f"{total_failed} failed, {batches_sent} batches sent successfully"
    )

    return {
        "message": "ETL processing complete",
        "total_animals": total_animals,
        "processed_animals": total_processed,
        "failed_animals": total_failed,
        "batches_sent": batches_sent,
        "total_batches": batch_number - 1,
    }
