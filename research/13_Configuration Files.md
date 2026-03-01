
# 13. Configuration Files

# Training config YAML
training_yaml = """# Training Configuration
experiment_name: "cnn-classifier-v1"
seed: 42

model:
  architecture: "resnet50"
  num_classes: 10
  pretrained: true
  dropout: 0.5
  freeze_backbone: false
  img_size: 224

training:
  epochs: 100
  batch_size: 32
  learning_rate: 0.001
  weight_decay: 0.0001
  scheduler: "cosine"
  label_smoothing: 0.1
  mixed_precision: true
  early_stopping_patience: 10
  gradient_clip: 1.0
  warmup_epochs: 5

data:
  train_dir: "data/train"
  val_dir: "data/val"
  test_dir: "data/test"
  num_workers: 4
  pin_memory: true
  augmentation: true

checkpoint_dir: "checkpoints"
log_dir: "logs"
mlflow_tracking_uri: "http://localhost:5000"
"""

# DVC config
dvc_config = """[core]
    autostage = true
    remote = s3-storage
['remote "s3-storage"']
    url = s3://cnn-mlops-data/dvc
    region = us-east-1
    access_key_id = ${AWS_ACCESS_KEY_ID}
    secret_access_key = ${AWS_SECRET_ACCESS_KEY}
"""

# Docker Compose for local development
docker_compose = """version: '3.8'

services:
  # MLflow Tracking Server
  mlflow:
    image: python:3.9-slim
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://cnn-mlops-models/mlflow
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    command: >
      bash -c "pip install mlflow psycopg2-binary boto3 && 
               mlflow server --host 0.0.0.0 --port 5000"
    depends_on:
      - postgres
    networks:
      - mlops-network

  # PostgreSQL for MLflow
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=mlflow
      - POSTGRES_PASSWORD=mlflow
      - POSTGRES_DB=mlflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - mlops-network

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - mlops-network

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - mlops-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - mlops-network

  # API Service
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/app/models/best_model.pt
      - CLASS_NAMES_PATH=/app/config/class_names.txt
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - REDIS_HOST=redis
      - LOG_LEVEL=INFO
    volumes:
      - ./models:/app/models:ro
      - ./config:/app/config:ro
    depends_on:
      - mlflow
      - redis
    networks:
      - mlops-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Streamlit App
  streamlit:
    build:
      context: .
      dockerfile: docker/Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    networks:
      - mlops-network

  # Jupyter Notebook
  jupyter:
    build:
      context: .
      dockerfile: docker/Dockerfile.jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/app/notebooks
      - ./data:/app/data
      - ./src:/app/src
    environment:
      - JUPYTER_ENABLE_LAB=yes
    networks:
      - mlops-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  mlops-network:
    driver: bridge
"""

# Prometheus config
prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cnn-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
"""

# Requirements files
requirements_main = """# Core dependencies
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0

# ML & Data
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
scipy>=1.10.0
albumentations>=1.3.0
opencv-python>=4.8.0
Pillow>=10.0.0
timm>=0.9.0

# API & Web
fastapi>=0.103.0
uvicorn[standard]>=0.23.0
python-multipart>=0.0.6
pydantic>=2.0.0
streamlit>=1.28.0

# MLOps
mlflow>=2.7.0
dvc[s3]>=3.0.0

# Monitoring
prometheus-client>=0.17.0
redis>=5.0.0

# Configuration
pyyaml>=6.0.1
python-dotenv>=1.0.0

# Utilities
tqdm>=4.66.0
python-json-logger>=2.0.7
requests>=2.31.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.17.0
"""

requirements_dev = """# Development dependencies
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
black>=23.0.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
bandit>=1.7.0
safety>=2.3.0
pre-commit>=3.4.0

# Documentation
sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0

# Testing
factory-boy>=3.3.0
faker>=19.0.0
"""

# Makefile
makefile_content = """.PHONY: help setup install dev-install test lint format clean docker-build docker-up docker-down train deploy

# Default target
help:
	@echo "CNN MLOps Platform - Available Commands:"
	@echo "  setup          - Initial project setup"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install    - Install development dependencies"
	@echo "  test           - Run all tests"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code with black"
	@echo "  clean          - Clean build artifacts"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-up      - Start Docker services"
	@echo "  docker-down    - Stop Docker services"
	@echo "  train          - Run training pipeline"
	@echo "  deploy-dev     - Deploy to development"
	@echo "  deploy-prod    - Deploy to production"

# Setup
setup:
	python -m venv venv
	$(MAKE) dev-install
	pre-commit install
	@echo "Setup complete! Activate virtual environment: source venv/bin/activate"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-e2e:
	pytest tests/e2e -v

# Code Quality
lint:
	flake8 src/ tests/ --max-line-length=100
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/ --ignore-missing-imports
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Cleaning
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "htmlcov" -delete
	rm -rf build/ dist/ *.egg-info/

# Docker
docker-build:
	docker-compose -f docker-compose.yml build

docker-up:
	docker-compose -f docker-compose.yml up -d

docker-down:
	docker-compose -f docker-compose.yml down

docker-logs:
	docker-compose -f docker-compose.yml logs -f

# Training
train:
	python -m src.training.train --config config/training.yaml

train-local:
	MLFLOW_TRACKING_URI=http://localhost:5000 python -m src.training.train --config config/training.yaml

# Data Management
data-pull:
	dvc pull

data-push:
	dvc push

data-status:
	dvc status

# MLflow
mlflow-ui:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns

# Deployment
deploy-dev:
	kubectl apply -k k8s/overlays/dev

deploy-prod:
	kubectl apply -k k8s/overlays/prod

undeploy-dev:
	kubectl delete -k k8s/overlays/dev

undeploy-prod:
	kubectl delete -k k8s/overlays/prod

# Infrastructure
infra-init:
	cd terraform && terraform init

infra-plan:
	cd terraform && terraform plan

infra-apply:
	cd terraform && terraform apply

infra-destroy:
	cd terraform && terraform destroy

# Utilities
notebook:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

api-docs:
	cd src/api && python -c "from main import app; import json; from fastapi.openapi.utils import get_openapi; print(json.dumps(get_openapi(title=app.title, version=app.version, routes=app.routes), indent=2))" > ../../docs/api/openapi.json
"""

# Write all config files
with open(f"{project_root}/config/training.yaml", "w") as f:
    f.write(training_yaml)

with open(f"{project_root}/dvc/config", "w") as f:
    f.write(dvc_config)

with open(f"{project_root}/docker-compose.yml", "w") as f:
    f.write(docker_compose)

with open(f"{project_root}/monitoring/prometheus.yml", "w") as f:
    f.write(prometheus_config)

with open(f"{project_root}/requirements.txt", "w") as f:
    f.write(requirements_main)

with open(f"{project_root}/requirements-dev.txt", "w") as f:
    f.write(requirements_dev)

with open(f"{project_root}/Makefile", "w") as f:
    f.write(makefile_content)

print("✅ Configuration files created (YAML, Docker Compose, Prometheus, Makefile)")
