"""
FastAPI endpoints for the Animal API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import HTTPException

from ..core.config import config, logger
from ..services.animal_service import process_all_animals_batch


async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": config.APP_VERSION,
        "service": config.APP_TITLE,
    }


async def get_animals(page: Optional[int] = 1):
    """Get paginated list of animals."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.ANIMALS_API_BASE_URL}/animals/v1/animals?page={page}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch animals"
                )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def get_animal_details(animal_id: int):
    """Get detailed information for a specific animal."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.ANIMALS_API_BASE_URL}/animals/v1/animals/{animal_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 404:
                    raise HTTPException(
                        status_code=404, detail=f"Animal with ID {animal_id} not found"
                    )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to fetch animal details",
                )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def receive_animals(animals: List[Dict[str, Any]]):
    """Receive and process animal data batches."""
    try:
        if len(animals) > config.MAX_ANIMALS_PER_BATCH:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {config.MAX_ANIMALS_PER_BATCH} animals per batch"
            )
        logger.info(f"Received batch of {len(animals)} animals")
        for animal in animals:
            logger.info(f"Processing animal: {animal.get('id', 'unknown')}")

        return {
            "message": f"Successfully received {len(animals)} animals",
            "count": len(animals),
        }
    except HTTPException:
        raise  # Re-raise HTTPExceptions without wrapping them
    except Exception as e:
        logger.error(f"Error processing animals: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing animals: {str(e)}"
        )


async def process_all_animals():
    """Process all animals from the external API."""
    try:
        return await process_all_animals_batch(config.ANIMALS_API_BASE_URL)
    except Exception as e:
        logger.error(f"Error in process_all_animals: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
