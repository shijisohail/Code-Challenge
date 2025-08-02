import logging
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException

from utils import (
    chunk_list,
    fetch_and_transform_animals,
    get_all_animal_ids,
    post_batch_with_retry,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Animal API",
    description="API to fetch animals from the animals service",
    version="1.0.0",
)

ANIMALS_API_BASE_URL = "http://localhost:3123"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "service": "Animal API",
    }


@app.get("/animals")
async def get_animals(page: Optional[int] = 1):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ANIMALS_API_BASE_URL}/animals/v1/animals?page={page}"
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


@app.get("/animals/{animal_id}")
async def get_animal_details(animal_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ANIMALS_API_BASE_URL}/animals/v1/animals/{animal_id}"
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


@app.post("/animals/v1/home")
async def receive_animals(animals: List[Dict[str, Any]]):
    try:
        if len(animals) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 animals per batch")
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


@app.post("/process-all-animals")
async def process_all_animals():
    try:
        logger.info("Starting to process all animals")

        animal_ids = await get_all_animal_ids(ANIMALS_API_BASE_URL)
        if not animal_ids:
            return {
                "message": "No animals found",
                "total_animals": 0,
                "batches_sent": 0,
                "failed_animals": 0,
            }

        transformed_animals = await fetch_and_transform_animals(
            ANIMALS_API_BASE_URL, animal_ids
        )

        batches = chunk_list(transformed_animals, 100)
        batches_sent = 0
        failed_animals = len(animal_ids) - len(transformed_animals)

        async with aiohttp.ClientSession() as session:
            for batch in batches:
                success = await post_batch_with_retry(
                    session, ANIMALS_API_BASE_URL, batch
                )
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

    except Exception as e:
        logger.error(f"Error in process_all_animals: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
