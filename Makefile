# Solar Panel Classifier — Makefile
# Common automation commands for development and deployment

.PHONY: help setup install dev-install format lint test train api streamlit docker-build docker-up docker-down clean

help: ## Show this help message
	@echo "Solar Panel Classifier — Available Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Create virtual environment and install dependencies
	python -m venv .venv
	.venv\Scripts\pip install -r requirements.txt

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install black flake8 isort mypy pytest pytest-asyncio httpx

format: ## Format code with black and isort
	black src/ tests/ app.py main.py train.py
	isort src/ tests/ app.py main.py train.py

lint: ## Run linters (flake8, mypy)
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203
	mypy src/ --ignore-missing-imports

test: ## Run test suite
	pytest tests/ -v --tb=short

train: ## Run training pipeline
	python train.py --model efficientnet --epochs 20

api: ## Start FastAPI inference server
	python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

streamlit: ## Start Streamlit web app
	streamlit run app.py

docker-build: ## Build Docker images
	docker build -f docker/Dockerfile -t solar-panel-classifier:latest .
	docker build -f docker/Dockerfile.dev -t solar-panel-classifier:dev .

docker-up: ## Start services with docker-compose
	docker-compose up --build -d

docker-down: ## Stop docker-compose services
	docker-compose down

clean: ## Remove temp files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "_temp_*.jpg" -delete
	rm -rf .pytest_cache .mypy_cache
