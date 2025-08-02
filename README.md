# Animal Processing API

A robust FastAPI application that processes animal data with retry logic and error handling.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python run_server.py
```

## API Endpoints

- `GET /animals` - List animals with pagination
- `GET /animals/{animal_id}` - Get specific animal details  
- `POST /animals/v1/home` - Receive transformed animal batches (max 100)
- `POST /process-all-animals` - Process all animals from external API

## Features

- Handles server errors (500, 502, 503, 504) with exponential backoff
- Manages server pauses (5-15 seconds) with extended timeouts
- Concurrent processing with rate limiting
- Automatic data transformation (friends arrays, ISO8601 timestamps)
