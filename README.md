# ETL Animal API

A comprehensive FastAPI application designed to process and manage animal data with robust error handling, concurrency support, and production-ready features. This application serves as both a proxy API for external animal services and a data processing pipeline with transformation capabilities.

## Quick Start

### Installation
```bash
# Install production dependencies
pip install -r requirements.txt

# Or install with development dependencies
make install-dev
```

### Running the Application
```bash
# Start the development server
python run_server.py

# Or use the Makefile
make run
```

### Health Check
```bash
# Check if the application is running
curl http://localhost:8000/health

# Or use the Makefile
make health
```

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, Windows
- **Memory**: Minimum 512MB RAM
- **Network**: Internet access for external API calls

## Core Dependencies

- **FastAPI (0.116.1)**: Modern web framework for building APIs
- **Uvicorn (0.24.0)**: ASGI server implementation
- **AioHTTP (3.9.1)**: Asynchronous HTTP client for external API calls
- **Pydantic (2.11.7)**: Data validation and settings management

## Project Architecture

### File Structure and Functions

```
Code-Challenge/
├── main.py                    # FastAPI application with API endpoints
├── utils.py                   # Utility functions for data processing and HTTP operations
├── run_server.py              # Server startup script
├── test_file.py               # Comprehensive test suite
├── requirements.txt           # Production dependencies
├── pyproject.toml             # Project configuration and development tools
├── Makefile                   # Development automation commands
├── .flake8                    # Flake8 linting configuration
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── .gitignore                 # Git ignore patterns
└── .github/workflows/ci.yml   # GitHub Actions CI/CD pipeline
```

### Detailed File Descriptions

#### **main.py**
The central FastAPI application file containing all API endpoints and request handling logic.

**Functions:**
- `health_check()`: Returns service health status and metadata
- `get_animals(page)`: Proxies paginated animal list requests to external API
- `get_animal_details(animal_id)`: Fetches specific animal details by ID
- `receive_animals(animals)`: Accepts and validates animal data batches (max 100)
- `process_all_animals()`: Orchestrates complete animal processing pipeline

**Key Features:**
- Comprehensive error handling with proper HTTP status codes
- Input validation using Pydantic models
- Asynchronous request processing
- Logging for monitoring and debugging

#### **utils.py**
Utility module containing core business logic for data processing and HTTP operations.

**Data Transformation Functions:**
- `transform_animal(animal)`: Main transformation function for animal data
- `_transform_friends(friends)`: Converts friend data from string to list format
- `_transform_born_at(born_at)`: Normalizes timestamps to ISO format
- `_parse_datetime_string(born_at)`: Handles multiple datetime format parsing

**HTTP Operations Functions:**
- `fetch_with_retry(session, url, max_retries)`: Robust HTTP client with retry logic
- `get_all_animal_ids(base_url)`: Paginates through all animals to collect IDs
- `fetch_and_transform_animals(base_url, animal_ids)`: Concurrent animal fetching with transformation
- `post_batch_with_retry(session, base_url, animals)`: Reliable batch posting with retries

**Helper Functions:**
- `chunk_list(lst, chunk_size)`: Splits lists into manageable chunks
- `_handle_http_response()`: Processes HTTP responses with proper error handling
- `_handle_timeout_error()`: Manages timeout scenarios with exponential backoff
- `_handle_client_error()`: Handles client-side connection errors

**Key Features:**
- Semaphore-based concurrency control to prevent server overload
- Exponential backoff retry strategy for failed requests
- Comprehensive error logging and monitoring
- Batch processing to optimize performance

#### **run_server.py**
Simple server startup script that launches the FastAPI application using Uvicorn.

**Configuration:**
- Host: 0.0.0.0 (allows external connections)
- Port: 8000 (standard development port)
- Reload: True (enables hot reloading during development)

#### **test_file.py**
Comprehensive test suite covering all application functionality with proper async mocking.

**Test Classes:**
- `TestHealthEndpoint`: Validates health check functionality
- `TestReceiveAnimalsEndpoint`: Tests animal data reception and validation
- `TestExternalAPIEndpoints`: Tests external API integration with mocking
- `TestUtilityFunctions`: Unit tests for data transformation functions

**Testing Features:**
- Async/await testing with proper mocking
- FastAPI TestClient integration
- Error scenario validation
- Data transformation verification

#### **pyproject.toml**
Comprehensive project configuration file managing dependencies and development tools.

**Configuration Sections:**
- Project metadata and dependencies
- Black code formatting settings
- isort import sorting configuration
- Flake8 linting rules and exclusions
- MyPy type checking configuration
- Bandit security scanning settings
- Coverage reporting configuration
- Pytest testing framework setup

#### **Makefile**
Development automation providing convenient commands for common tasks.

**Available Commands:**
- `make install`: Install production dependencies
- `make install-dev`: Install development dependencies
- `make setup-dev`: Complete development environment setup
- `make format`: Format code using Black and isort
- `make lint`: Run all linters (flake8, mypy, bandit)
- `make test`: Execute test suite
- `make test-cov`: Run tests with coverage reporting
- `make ci`: Complete CI pipeline (format, lint, test)
- `make run`: Start development server
- `make health`: Check application health
- `make clean`: Remove generated files and caches
- `make pre-commit`: Install pre-commit hooks

#### **.flake8**
Flake8 linting configuration optimized for development productivity.

**Configuration:**
- Line length: 88 characters (Black compatibility)
- Complexity limit: 10
- Ignores docstring requirements for faster development
- Excludes common directories (venv, build, etc.)

#### **.pre-commit-config.yaml**
Pre-commit hooks configuration ensuring code quality before commits.

**Hooks:**
- Code formatting (Black, isort)
- Linting (flake8, mypy)
- Security scanning (bandit)
- General file checks (trailing whitespace, YAML syntax)

## API Documentation

### Endpoints

#### Health Check
```
GET /health
```
Returns service health status, version, and timestamp.

#### List Animals
```
GET /animals?page={page_number}
```
Retrieves paginated list of animals from external service.

#### Animal Details
```
GET /animals/{animal_id}
```
Fetches detailed information for a specific animal.

#### Receive Animals
```
POST /animals/v1/home
Content-Type: application/json

[{"id": 1, "name": "Fluffy", "type": "cat"}]
```
Accepts animal data batches (maximum 100 animals per request).

#### Process All Animals
```
POST /process-all-animals
```
Initiates complete animal processing pipeline including fetching, transformation, and batching.

## Development Workflow

### Setting Up Development Environment
```bash
# Clone repository
git clone <repository-url>
cd Code-Challenge

# Setup development environment
make setup-dev
```

### Code Quality Assurance
```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Complete CI pipeline
make ci
```

### Pre-commit Hooks
Pre-commit hooks automatically run code quality checks before each commit:
```bash
# Install hooks (done automatically with setup-dev)
make pre-commit

# Run hooks manually
pre-commit run --all-files
```

## Testing Strategy

### Test Categories
- **Unit Tests**: Individual function validation
- **Integration Tests**: API endpoint testing with mocked external services
- **Error Handling Tests**: Validation of error scenarios and edge cases

### Running Tests
```bash
# Basic test run
make test

# Tests with coverage
make test-cov

# View coverage report
open htmlcov/index.html
```

## Performance Characteristics

### Concurrency
- **Semaphore Control**: Limits concurrent requests to prevent server overload
- **Batch Processing**: Handles large datasets efficiently
- **Connection Pooling**: Optimizes HTTP connection reuse

### Error Resilience
- **Retry Logic**: Exponential backoff for failed requests
- **Timeout Handling**: Configurable timeouts for different scenarios
- **Circuit Breaking**: Fails fast when external services are unavailable

### Memory Management
- **Batch Processing**: Prevents memory overflow with large datasets
- **Connection Limits**: Controls resource usage
- **Garbage Collection**: Proper cleanup of resources

## Monitoring and Logging

### Log Levels
- **INFO**: General application flow
- **WARNING**: Recoverable errors and retries
- **ERROR**: Serious errors requiring attention

### Key Metrics
- Request processing times
- Error rates and types
- Batch processing statistics
- External API response times

## Security Considerations

- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Prevents information leakage in error responses
- **Security Scanning**: Bandit integration for vulnerability detection
- **Dependency Management**: Regular security updates

## Deployment

### Docker Support
```bash
# Build container
docker build -t animal-api .

# Run container
docker run -p 8000:8000 animal-api
```

### Environment Variables
- `ANIMALS_API_BASE_URL`: External API base URL (default: http://localhost:3123)
- `MAX_CONCURRENT_REQUESTS`: Concurrency limit (default: 10)
- `LOG_LEVEL`: Logging level (default: INFO)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Run `make ci` to ensure quality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.
