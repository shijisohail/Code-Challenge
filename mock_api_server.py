#!/usr/bin/env python3
"""
Simple mock API server to provide animal data for testing the main API.

This server runs on port 3123 and provides the endpoints that the main API expects.
"""

from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Mock Animals API", version="1.0.0")

# Sample animal data (reduced for clearer testing)
ANIMALS = {
    1: {
        "id": 1,
        "name": "Fluffy",
        "type": "cat",
        "breed": "Persian",
        "age": 3,
        "friends": "Whiskers",
        "born_at": "2021-01-15T10:30:00Z",
        "weight": 4.5,
    },
    2: {
        "id": 2,
        "name": "Buddy",
        "type": "dog",
        "breed": "Golden Retriever",
        "age": 5,
        "friends": "Max",
        "born_at": "2019-03-20T14:15:00Z",
        "weight": 25.3,
    },
    3: {
        "id": 3,
        "name": "Whiskers",
        "type": "cat",
        "breed": "Siamese",
        "age": 2,
        "friends": "Fluffy",
        "born_at": "2022-05-10T08:45:00Z",
        "weight": 3.8,
    },
}

# Store for received animal batches
received_batches = []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Mock Animals API",
    }


@app.get("/animals/v1/animals")
async def get_animals(page: int = 1):
    """Get paginated list of animal IDs"""
    page_size = 2  # Small page size for testing
    start_idx = (page - 1) * page_size

    animal_ids = list(ANIMALS.keys())
    total_animals = len(animal_ids)

    if start_idx >= total_animals:
        return {"items": [], "page": page, "total": total_animals, "has_more": False}

    end_idx = min(start_idx + page_size, total_animals)
    page_ids = animal_ids[start_idx:end_idx]

    return {
        "items": [{"id": animal_id} for animal_id in page_ids],
        "page": page,
        "total": total_animals,
        "has_more": end_idx < total_animals,
    }


@app.get("/animals/v1/animals/{animal_id}")
async def get_animal_details(animal_id: int):
    """Get detailed information for a specific animal"""
    if animal_id not in ANIMALS:
        raise HTTPException(
            status_code=404, detail=f"Animal with ID {animal_id} not found"
        )

    return ANIMALS[animal_id]


@app.post("/animals/v1/home")
async def receive_animals(animals: List[Dict[str, Any]]):
    """Receive processed animal batches"""
    print(f"Received batch of {len(animals)} animals:")
    for animal in animals:
        print(
            f"  - {animal.get('name', 'Unknown')} (ID: {animal.get('id', 'Unknown')})"
        )

    received_batches.append(
        {
            "timestamp": datetime.now().isoformat(),
            "count": len(animals),
            "animals": animals,
        }
    )

    return {
        "message": f"Successfully received {len(animals)} animals",
        "batch_id": len(received_batches),
    }


@app.get("/debug/received-batches")
async def get_received_batches():
    """Debug endpoint to see received batches"""
    return {"total_batches": len(received_batches), "batches": received_batches}


if __name__ == "__main__":
    print("🐾 Starting Mock Animals API server on port 3123...")
    print("📋 Available endpoints:")
    print("  GET  /health")
    print("  GET  /animals/v1/animals?page={page}")
    print("  GET  /animals/v1/animals/{animal_id}")
    print("  POST /animals/v1/home")
    print("  GET  /debug/received-batches")
    print("🚀 Server starting...")

    uvicorn.run(app, host="0.0.0.0", port=3123, log_level="info")
