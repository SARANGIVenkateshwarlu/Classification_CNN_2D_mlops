import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

project_name = "classification-cnn-2d-mlops"

list_of_files = [

    # ======================
    # CI/CD
    # ======================
    ".github/workflows/ci-cd.yml",

    # ======================
    # Docker
    # ======================
    "docker/Dockerfile",
    "docker/Dockerfile.dev",

    # ======================
    # Kubernetes
    # ======================
    "k8s/base/deployment.yaml",
    "k8s/base/service.yaml",
    "k8s/base/ingress.yaml",
    "k8s/overlays/dev/kustomization.yaml",
    "k8s/overlays/prod/kustomization.yaml",

    # ======================
    # Terraform (AWS Infra)
    # ======================
    "terraform/main.tf",
    "terraform/variables.tf",
    "terraform/outputs.tf",
    "terraform/providers.tf",

    # ======================
    # Source Code
    # ======================
    f"src/{project_name}/__init__.py",

    # API
    f"src/{project_name}/api/__init__.py",
    f"src/{project_name}/api/main.py",

    # Models
    f"src/{project_name}/models/__init__.py",
    f"src/{project_name}/models/cnn_classifier.py",

    # Training
    f"src/{project_name}/training/__init__.py",
    f"src/{project_name}/training/train.py",

    # Data
    f"src/{project_name}/data/__init__.py",
    f"src/{project_name}/data/dataset.py",

    # Monitoring
    f"src/{project_name}/monitoring/__init__.py",
    f"src/{project_name}/monitoring/drift_detector.py",

    # Utils
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/logger.py",
    f"src/{project_name}/utils/metrics.py",
    f"src/{project_name}/utils/config.py",

    # ======================
    # Streamlit UI
    # ======================
    "streamlit_app/main.py",

    # ======================
    # Tests
    # ======================
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    "tests/e2e/__init__.py",

    # ======================
    # Docs
    # ======================
    "docs/architecture.md",
    "docs/api_docs.md",

    # ======================
    # Project Root Files
    # ======================
    "docker-compose.yml",
    "Makefile",
    "pyproject.toml",
    "README.md",
    ".env",
    ".gitignore",
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, 'w') as f:
            pass
        logging.info(f"Creating empty file: {filepath}")
    else:
        logging.info(f"{filename} already exists")