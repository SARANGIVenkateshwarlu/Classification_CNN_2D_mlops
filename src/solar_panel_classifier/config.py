"""Configuration and constants for the Solar Panel Classifier."""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "Data"
MODELS_DIR = PROJECT_ROOT / "models"
CONFIG_DIR = PROJECT_ROOT / "config"

# Image preprocessing constants
IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_SIZE = (IMG_HEIGHT, IMG_WIDTH)
BATCH_SIZE = 32
SEED = 42

# Class names (must match folder names in Data/)
CLASS_NAMES = [
    "Bird-drop",
    "Clean",
    "Dusty",
    "Electrical-damage",
    "Physical-Damage",
    "Snow-Covered",
]

NUM_CLASSES = len(CLASS_NAMES)

# Default model path (best model)
DEFAULT_MODEL_PATH = MODELS_DIR / "trained_effnet_finetune.keras"

# Fallback model paths
MODEL_PATHS = {
    "efficientnet": MODELS_DIR / "trained_effnet_finetune.keras",
    "efficientnet_h5": MODELS_DIR / "trained_effnet_finetune.h5",
    "mobilenetv2": MODELS_DIR / "mobilenetv2_2.keras",
    "mobilenetv2_h5": MODELS_DIR / "mobilenetv2_2.h5",
}

# Training constants
VALIDATION_SPLIT = 0.2
EPOCHS = 20
LEARNING_RATE = 3e-4


def get_model_path(model_name: str = "efficientnet") -> Path:
    """Resolve model path by name."""
    path = MODEL_PATHS.get(model_name, DEFAULT_MODEL_PATH)
    if path.exists():
        return path
    # Try .h5 fallback
    fallback = MODEL_PATHS.get(f"{model_name}_h5", DEFAULT_MODEL_PATH)
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Model not found: {path}")
