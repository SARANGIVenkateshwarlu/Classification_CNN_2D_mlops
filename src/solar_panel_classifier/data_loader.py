"""Image preprocessing and data loading utilities."""

import numpy as np
from pathlib import Path
from typing import Union, Tuple, List
from PIL import Image

from .config import IMG_SIZE, CLASS_NAMES, BATCH_SIZE, SEED, VALIDATION_SPLIT


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """Load and preprocess a single image for inference.

    Args:
        image_path: Path to the image file.

    Returns:
        Preprocessed image array of shape (1, 224, 224, 3).
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def preprocess_efficientnet(image_array: np.ndarray) -> np.ndarray:
    """Apply EfficientNet preprocessing (same as preprocess_input)."""
    from tensorflow.keras.applications.efficientnet import preprocess_input
    return preprocess_input(image_array)


def preprocess_mobilenet(image_array: np.ndarray) -> np.ndarray:
    """Apply MobileNetV2 preprocessing (normalize to [-1, 1])."""
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    return preprocess_input(image_array)


def preprocess_rescale(image_array: np.ndarray) -> np.ndarray:
    """Simple rescaling to [0, 1]."""
    return image_array / 255.0


def create_tf_dataset(
    data_dir: Union[str, Path],
    subset: str = "training",
    image_size: Tuple[int, int] = IMG_SIZE,
    batch_size: int = BATCH_SIZE,
    seed: int = SEED,
    validation_split: float = VALIDATION_SPLIT,
):
    """Create a TensorFlow dataset from directory.

    Args:
        data_dir: Root directory containing class subfolders.
        subset: 'training' or 'validation'.
        image_size: Target image size.
        batch_size: Batch size.
        seed: Random seed.
        validation_split: Fraction of data for validation.

    Returns:
        tf.data.Dataset object.
    """
    import tensorflow as tf

    return tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=validation_split,
        subset=subset,
        image_size=image_size,
        batch_size=batch_size,
        seed=seed,
    )


def get_class_weights(data_dir: Union[str, Path]) -> dict:
    """Compute class weights to handle imbalanced dataset.

    Args:
        data_dir: Root directory containing class subfolders.

    Returns:
        Dictionary mapping class index to weight.
    """
    data_dir = Path(data_dir)
    class_counts = {}
    total = 0

    for idx, class_name in enumerate(CLASS_NAMES):
        class_path = data_dir / class_name
        if class_path.exists():
            count = len(list(class_path.glob("*")))
            class_counts[idx] = count
            total += count

    num_classes = len(CLASS_NAMES)
    weights = {
        idx: total / (num_classes * count)
        for idx, count in class_counts.items()
    }
    return weights


def create_data_augmentation():
    """Create a data augmentation pipeline."""
    import tensorflow as tf

    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.15),
            tf.keras.layers.RandomZoom(0.15),
        ],
        name="data_augmentation",
    )
