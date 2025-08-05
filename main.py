from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from app.api import endpoints
from app.core.config import config

app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return await endpoints.health_check()


@app.get("/animals")
async def get_animals(page: Optional[int] = 1) -> Dict[str, Any]:
    return await endpoints.get_animals(page)


@app.get("/animals/{animal_id}")
async def get_animal_details(animal_id: int) -> Dict[str, Any]:
    return await endpoints.get_animal_details(animal_id)


@app.post("/animals/v1/home")
async def receive_animals(animals: List[Dict[str, Any]]) -> Dict[str, Any]:
    return await endpoints.receive_animals(animals)


@app.post("/process-all-animals")
async def process_all_animals() -> Dict[str, Any]:
    return await endpoints.process_all_animals()
