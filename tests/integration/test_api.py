"""Integration tests for FastAPI inference service."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Solar Panel Classifier API"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data


@pytest.mark.skipif(not TF_AVAILABLE, reason="TensorFlow not installed")
def test_model_info_endpoint(client):
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    assert "num_classes" in data
