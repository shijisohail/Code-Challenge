.PHONY: help install install-dev format lint test test-cov clean run health pre-commit setup-dev ci docker-build docker-run docker-dev docker-stop docker-clean docker-logs

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  setup-dev    - Full development setup (install + pre-commit)"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run all linters (flake8, mypy, bandit)"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  ci           - Run complete CI pipeline (format, lint, test)"
	@echo "  run          - Start the development server"
	@echo "  health       - Check application health"
	@echo "  clean        - Clean up generated files"
	@echo "  pre-commit   - Install pre-commit hooks"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run application in Docker (production)"
	@echo "  docker-dev   - Run application in Docker (development)"
	@echo "  docker-stop  - Stop all Docker containers"
	@echo "  docker-clean - Clean up Docker resources"
	@echo "  docker-logs  - View Docker container logs"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install -e .[dev] || echo "Warning: Optional dev dependencies not available"
	@echo "✅ Development dependencies installed!"

setup-dev: install-dev pre-commit
	@echo "Development environment setup complete!"

# Formatting
format:
	@echo "🎨 Formatting code..."
	black .
	isort .
	@echo "✅ Code formatting complete!"

# Linting
lint:
	@echo "🔍 Running linters..."
	flake8 .
	mypy .
	bandit -r . -f json -o bandit-report.json || bandit -r .
	@echo "✅ Linting complete!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest -v
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov --cov-report=term-missing --cov-report=html
	@echo "✅ Tests with coverage complete!"
	@echo "📊 Coverage report: htmlcov/index.html"

# CI Pipeline
ci: format lint test-cov
	@echo "🚀 CI pipeline complete!"

# Development server
run:
	@echo "🚀 Starting development server..."
	python run_server.py

# Health check
health:
	@echo "🏥 Checking application health..."
	curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .flake8_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -f .coverage
	rm -f coverage.xml
	rm -f bandit-report.json
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete!"

# Pre-commit
pre-commit:
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t animal-api:latest .
	@echo "✅ Docker image built successfully!"

docker-run:
	@echo "🐳 Running application in Docker (production)..."
	docker-compose up -d animal-api
	@echo "✅ Application running at http://localhost:8000"
	@echo "🏥 Health check: make docker-health"

docker-dev:
	@echo "🐳 Running application in Docker (development)..."
	docker-compose --profile dev up -d animal-api-dev
	@echo "✅ Development server running at http://localhost:8000"
	@echo "🔄 Hot reloading enabled"

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped!"

docker-clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v --rmi local
	docker system prune -f
	@echo "✅ Docker cleanup complete!"

docker-logs:
	@echo "📋 Viewing Docker container logs..."
	docker-compose logs -f animal-api

docker-health:
	@echo "🏥 Checking Docker container health..."
	docker-compose exec animal-api curl -f http://localhost:8000/health || echo "❌ Health check failed"

docker-shell:
	@echo "🐚 Opening shell in Docker container..."
	docker-compose exec animal-api /bin/bash
