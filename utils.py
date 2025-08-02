import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


def transform_animal(animal: Dict[str, Any]) -> Dict[str, Any]:
    transformed = animal.copy()
    if "friends" in transformed and transformed["friends"]:
        if isinstance(transformed["friends"], str):
            transformed["friends"] = [
                friend.strip()
                for friend in transformed["friends"].split(",")
                if friend.strip()
            ]
    else:
        transformed["friends"] = []

    if "born_at" in transformed and transformed["born_at"] is not None:
        try:
            born_at = transformed["born_at"]
            if isinstance(born_at, (int, float)):
                dt = datetime.utcfromtimestamp(born_at / 1000.0)
                transformed["born_at"] = dt.isoformat() + "Z"
            elif isinstance(born_at, str):
                # Try common datetime formats
                formats = [
                    "%Y-%m-%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(born_at, fmt)
                        transformed["born_at"] = dt.isoformat() + "Z"
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"Could not parse born_at: {born_at}")
                    transformed["born_at"] = None
        except Exception as e:
            logger.warning(f"Error transforming born_at: {e}")
            transformed["born_at"] = None

    return transformed


async def fetch_with_retry(
    session: aiohttp.ClientSession, url: str, max_retries: int = 5
) -> Optional[Dict]:
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=20, connect=5)

            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 404:
                    return None
                if response.status in [500, 502, 503, 504]:
                    wait_time = min(2**attempt, 16)  # Cap at 16 seconds
                    logger.warning(
                        f"Server error {response.status} for {url}, "
                        f"attempt {attempt + 1}/{max_retries}, "
                        f"waiting {wait_time}s"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Unexpected status {response.status} for {url}")
                return None

        except asyncio.TimeoutError:
            # Progressive wait for timeouts
            wait_time = min(3 + attempt * 2, 10)
            logger.warning(
                f"Timeout for {url} (server may be pausing), "
                f"attempt {attempt + 1}/{max_retries}, "
                f"waiting {wait_time}s"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)

        except aiohttp.ClientError as e:
            logger.warning(
                f"Connection error for {url}: {e}, "
                f"attempt {attempt + 1}/{max_retries}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None

    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None


async def get_all_animal_ids(base_url: str) -> List[int]:
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
    base_url: str, animal_ids: List[int], max_concurrent: int = 10
) -> List[Dict[str, Any]]:
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
                f"Processing batch {i//batch_size + 1}: "
                f"animals {i+1}-{min(i+batch_size, len(animal_ids))}"
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
                elif result is not None:
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


async def post_batch_with_retry(
    session: aiohttp.ClientSession,
    base_url: str,
    animals: List[Dict],
    max_retries: int = 5,
) -> bool:
    url = f"{base_url}/animals/v1/home"

    for attempt in range(max_retries):
        try:
            async with session.post(
                url,
                json=animals,
                timeout=aiohttp.ClientTimeout(total=60),
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status in [200, 201, 202]:
                    logger.info(f"Successfully sent batch of {len(animals)} animals")
                    return True
                if response.status in [500, 502, 503, 504]:
                    logger.warning(
                        f"Server error {response.status}, "
                        f"attempt {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
                    continue
                logger.error(f"Failed to send batch: {response.status}")
                return False
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout sending batch, attempt {attempt + 1}/{max_retries}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)

    logger.error(f"Failed to send batch after {max_retries} attempts")
    return False


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]
