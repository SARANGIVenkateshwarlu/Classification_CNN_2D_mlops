"""
Solar Panel Condition Classifier — Enterprise Setup
=====================================================
Production-grade package setup with MLOps tooling support.

Usage:
    pip install -e .
    pip install -e ".[dev]"
    pip install -e ".[api]"
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Extra dependencies
DEV_REQUIRES = [
    "black>=24.0",
    "flake8>=7.0",
    "isort>=5.13",
    "mypy>=1.8",
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "httpx>=0.27",
]

API_REQUIRES = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",
    "prometheus-client>=0.20",
]

MONITORING_REQUIRES = [
    "prometheus-client>=0.20",
    "evidently>=0.4",
    "mlflow>=2.11",
]

AWS_REQUIRES = [
    "boto3>=1.34",
    "s3fs>=2024.1",
]

ALL_REQUIRES = DEV_REQUIRES + API_REQUIRES + MONITORING_REQUIRES + AWS_REQUIRES

setup(
    name="solar-panel-classifier",
    version="0.1.0",
    author="Krish AI Projects",
    author_email="krish.ai@example.com",
    description="2D CNN-based image classification for solar panel condition monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/Classification_CNN_2D",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": DEV_REQUIRES,
        "api": API_REQUIRES,
        "monitoring": MONITORING_REQUIRES,
        "aws": AWS_REQUIRES,
        "all": ALL_REQUIRES,
    },
    entry_points={
        "console_scripts": [
            "solar-panel-classifier=main:main",
            "solar-panel-train=train:main",
            "solar-panel-api=src.api.main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
