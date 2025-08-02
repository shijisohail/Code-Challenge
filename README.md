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

## 📚 Dependencies

- Python 3.8+
- FastAPI
- Uvicorn
- AioHTTP
- Pydantic

Check `pyproject.toml` or `requirements.txt` for full list and versions.

## ❓ How to Test

- Run unit tests using `pytest`
- For async tests, use `pytest-asyncio`
- Coverage reports with `pytest-cov`

## 🔍 Linting & Formatting

- Code formatting with `black`
- Sort imports with `isort`
- Linting with `flake8`
- Security checks with `bandit`

## 🔄 CI/CD

CI/CD is managed through GitHub Actions with multiple Python versions and includes steps for setup, linting, testing, and deployment.

## 📁 Project Structure

```
Code-Challenge/
├── main.py                    # FastAPI application with endpoints
├── utils.py                   # Utility functions for data processing
├── run_server.py              # Server startup script
├── test_file.py               # Comprehensive test suite
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration and tool settings
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
└── .github/workflows/ci.yml   # GitHub Actions CI/CD pipeline
```

## 🏗️ Architecture Features

- **Async/await support**: Built with asyncio for efficient concurrent processing
- **Robust error handling**: Handles network timeouts, server errors, and retries
- **Rate limiting**: Semaphore-based concurrency control to avoid overwhelming servers
- **Data transformation**: Converts timestamps and normalizes friend lists
- **Batch processing**: Handles up to 100 animals per batch with chunking support

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
- **Linting**: Use `black`, `isort`, and `flake8` for code style
- **CI/CD**: Configured GitHub Actions for automated testing and deployment

## ⚖️ License
This project is licensed under the MIT License.
