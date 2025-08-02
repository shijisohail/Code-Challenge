from fastapi import FastAPI, HTTPException
import aiohttp
from typing import Optional

app = FastAPI(title="Animal API", description="API to fetch animals from the animals service")

ANIMALS_API_BASE_URL = "http://localhost:3123/animals/v1"

@app.get("/animals")
async def get_animals(page: Optional[int] = 1):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ANIMALS_API_BASE_URL}/animals?page={page}") as response:
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
            async with session.get(f"{ANIMALS_API_BASE_URL}/animals/{animal_id}") as response:
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
