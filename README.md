# Animal API

A FastAPI application to process and manage animal data with robust error handling and concurrency support.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**
   ```bash
   python run_server.py
   ```

## 📖 API Overview
- **Health Check**: `GET /health` - Verify service health
- **List Animals**: `GET /animals` - List animals with pagination
- **Animal Details**: `GET /animals/{animal_id}` - Fetch specific animal details
- **Receive Animals**: `POST /animals/v1/home` - Receive animal batches (max 100)
- **Process All**: `POST /process-all-animals` - Process all available animals

## ✨ Features
- **Resilient Networking**: Handles 500/502/503/504 errors with retries
- **Efficient Processing**: Supports concurrent requests with rate limits
- **Data Transformation**: Converts timestamps and formats friend lists

## 🛠️ Development
- **Testing**: Run `pytest` for unit tests
- **Linting**: Use `black`, `isort`, and `ruff` for code style
- **CI/CD**: Configured GitHub Actions for automated testing and deployment

## ⚖️ License
This project is licensed under the MIT License.
