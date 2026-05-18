"""Unit tests for data loader module."""

import numpy as np
from src.solar_panel_classifier.data_loader import (
    load_image,
    preprocess_rescale,
    get_class_weights,
)
from src.solar_panel_classifier.config import DATA_DIR


def test_preprocess_rescale():
    arr = np.array([0, 127, 255], dtype=np.float32)
    result = preprocess_rescale(arr)
    assert result[0] == 0.0
    assert result[2] == 1.0


def test_load_image_not_found():
    try:
        load_image("non_existent_file.jpg")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_get_class_weights():
    if DATA_DIR.exists():
        weights = get_class_weights(DATA_DIR)
        assert isinstance(weights, dict)
        assert len(weights) > 0
