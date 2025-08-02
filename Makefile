.PHONY: help install install-dev format lint test test-cov clean run health pre-commit setup-dev ci

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

# Installation
install:
	pip install -r requirements.txt


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
