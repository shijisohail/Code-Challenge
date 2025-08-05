"""
HTTP client service with retry logic and error handling.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from ..core.config import config

logger = logging.getLogger(__name__)


async def _handle_http_response(
    response: aiohttp.ClientResponse, url: str, attempt: int, max_retries: int
) -> Tuple[Optional[Dict], bool]:
    """Handle HTTP response and return (result, should_continue)."""
    if response.status == 200:
        return await response.json(), False

    if response.status == 404:
        return None, False

    if response.status in [500, 502, 503, 504]:
        wait_time = min(config.INITIAL_RETRY_DELAY**attempt, config.MAX_RETRY_DELAY)
        logger.warning(
            f"Server error {response.status} for {url}, "
            f"attempt {attempt + 1}/{max_retries}, "
            f"waiting {wait_time}s"
        )
        if attempt < max_retries - 1:
            await asyncio.sleep(wait_time)
        return None, True

    logger.error(f"Unexpected status {response.status} for {url}")
    return None, False


async def _handle_timeout_error(url: str, attempt: int, max_retries: int) -> bool:
    """Handle timeout error and return should_continue."""
    wait_time = min(3 + attempt * 2, 10)
    logger.warning(
        f"Timeout for {url} (server may be pausing), "
        f"attempt {attempt + 1}/{max_retries}, "
        f"waiting {wait_time}s"
    )
    if attempt < max_retries - 1:
        await asyncio.sleep(wait_time)
    return True


async def _handle_client_error(
    url: str, error: aiohttp.ClientError, attempt: int, max_retries: int
) -> bool:
    """Handle client error and return should_continue."""
    logger.warning(
        f"Connection error for {url}: {error}, " f"attempt {attempt + 1}/{max_retries}"
    )
    if attempt < max_retries - 1:
        await asyncio.sleep(config.INITIAL_RETRY_DELAY**attempt)
    return True


async def fetch_with_retry(
    session: aiohttp.ClientSession, url: str, max_retries: int = None
) -> Optional[Dict]:
    """Fetch URL with retry logic for handling various error conditions."""
    if max_retries is None:
        max_retries = config.MAX_RETRIES
        
    timeout = aiohttp.ClientTimeout(
        total=config.REQUEST_TIMEOUT, 
        connect=config.CONNECT_TIMEOUT
    )

    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                result, should_continue = await _handle_http_response(
                    response, url, attempt, max_retries
                )
                if not should_continue:
                    return result

        except asyncio.TimeoutError:
            should_continue = await _handle_timeout_error(url, attempt, max_retries)
            if not should_continue:
                break

        except aiohttp.ClientError as e:
            should_continue = await _handle_client_error(url, e, attempt, max_retries)
            if not should_continue:
                break

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None

    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None


async def post_batch_with_retry(
    session: aiohttp.ClientSession,
    base_url: str,
    animals: List[Dict],
    max_retries: int = None,
) -> bool:
    """Post animal batch with retry logic."""
    if max_retries is None:
        max_retries = config.MAX_RETRIES
        
    url = f"{base_url}/animals/v1/home"

    for attempt in range(max_retries):
        try:
            async with session.post(
                url,
                json=animals,
                timeout=aiohttp.ClientTimeout(total=config.BATCH_POST_TIMEOUT),
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
                        await asyncio.sleep(config.INITIAL_RETRY_DELAY**attempt)
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
