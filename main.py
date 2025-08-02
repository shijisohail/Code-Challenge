from fastapi import FastAPI, HTTPException
import aiohttp
import logging
from typing import Optional, List, Dict, Any
from utils import (
    get_all_animal_ids, 
    fetch_and_transform_animals, 
    chunk_list, 
    post_batch_with_retry
)

app = FastAPI(title="Animal API", description="API to fetch animals from the animals service")

ANIMALS_API_BASE_URL = "http://localhost:3123"
logger = logging.getLogger(__name__)

@app.get("/animals")
async def get_animals(page: Optional[int] = 1):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ANIMALS_API_BASE_URL}/animals/v1/animals?page={page}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch animals")
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/animals/{animal_id}")
async def get_animal_details(animal_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ANIMALS_API_BASE_URL}/animals/v1/animals/{animal_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail=f"Animal with ID {animal_id} not found")
                else:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch animal details")
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
            "count": len(animals)
        }
    except Exception as e:
        logger.error(f"Error processing animals: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing animals: {str(e)}")

