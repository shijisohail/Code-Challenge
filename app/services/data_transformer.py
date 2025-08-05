"""
Data transformation service for animal data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _transform_friends(friends: Any) -> List[str]:
    """Transform friends field to a list of strings."""
    if not friends:
        return []

    if isinstance(friends, str):
        return [friend.strip() for friend in friends.split(",") if friend.strip()]
    elif isinstance(friends, list):
        return [str(friend).strip() for friend in friends if str(friend).strip()]
    return []


def _parse_datetime_string(born_at: str) -> Optional[str]:
    """Parse datetime string using common formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%m-%d-%Y %H:%M:%S",  # MM-dd-yyyy format
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S+00:00",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(born_at, fmt)
            # Convert to UTC and return with +00:00 timezone
            return dt.isoformat().replace("+00:00", "") + "+00:00"
        except ValueError:
            continue

    logger.warning(f"Could not parse born_at: {born_at}")
    return None


def _transform_born_at(born_at: Any) -> Optional[str]:
    """Transform born_at field to ISO format."""
    if born_at is None:
        return None

    try:
        if isinstance(born_at, (int, float)):
            dt = datetime.utcfromtimestamp(born_at / 1000.0)
            return dt.isoformat() + "+00:00"
        elif isinstance(born_at, str):
            parsed = _parse_datetime_string(born_at)
            return parsed if parsed is not None else born_at
    except Exception as e:
        logger.warning(f"Error transforming born_at: {e}")

    return born_at


def transform_animal(animal: Dict[str, Any]) -> Dict[str, Any]:
    """Transform animal data with normalized friends and born_at fields."""
    transformed = animal.copy()

    # Transform friends field
    transformed["friends"] = _transform_friends(transformed.get("friends"))

    # Transform born_at field
    if "born_at" in transformed:
        transformed["born_at"] = _transform_born_at(transformed["born_at"])

    return transformed


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]
