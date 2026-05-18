"""Unit tests for configuration module."""

from src.solar_panel_classifier.config import CLASS_NAMES, NUM_CLASSES, IMG_SIZE


def test_class_names():
    assert len(CLASS_NAMES) == 6
    assert "Clean" in CLASS_NAMES
    assert "Bird-drop" in CLASS_NAMES


def test_num_classes():
    assert NUM_CLASSES == 6


def test_image_size():
    assert IMG_SIZE == (224, 224)
