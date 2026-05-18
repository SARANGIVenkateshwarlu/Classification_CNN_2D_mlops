"""Model loading and inference utilities."""

import numpy as np
from pathlib import Path
from typing import Union, List, Tuple, Optional

from .config import (
    CLASS_NAMES,
    NUM_CLASSES,
    DEFAULT_MODEL_PATH,
    get_model_path,
)
from .data_loader import load_image, preprocess_efficientnet


class SolarPanelClassifier:
    """Solar Panel Image Classifier for inference.

    Supports EfficientNetB0 and MobileNetV2 models trained on
    6-class solar panel condition dataset.

    Classes:
        - Bird-drop
        - Clean
        - Dusty
        - Electrical-damage
        - Physical-Damage
        - Snow-Covered
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        model_name: Optional[str] = None,
    ):
        """Initialize classifier with a trained model.

        Args:
            model_path: Direct path to a .keras or .h5 model file.
            model_name: Name of a known model ('efficientnet' or 'mobilenetv2').
                        Ignored if model_path is provided.
        """
        import tensorflow as tf

        self._tf = tf

        if model_path is not None:
            self.model_path = Path(model_path)
        elif model_name is not None:
            self.model_path = get_model_path(model_name)
        else:
            self.model_path = DEFAULT_MODEL_PATH

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                f"Please ensure trained models are placed in the 'models/' directory."
            )

        self.model = self._load_model()
        self.class_names = CLASS_NAMES
        self.num_classes = NUM_CLASSES

    def _load_model(self):
        """Load the Keras model from disk."""
        print(f"Loading model from: {self.model_path}")
        model = self._tf.keras.models.load_model(str(self.model_path))
        print("Model loaded successfully.")
        return model

    def predict(
        self,
        image_input: Union[str, Path, np.ndarray],
        top_k: int = 1,
    ) -> List[Tuple[str, float]]:
        """Predict class for a single image.

        Args:
            image_input: Path to image file or preprocessed image array.
            top_k: Number of top predictions to return.

        Returns:
            List of (class_name, confidence) tuples, sorted by confidence.
        """
        if isinstance(image_input, (str, Path)):
            image = load_image(image_input)
        else:
            image = image_input
            if image.ndim == 3:
                image = np.expand_dims(image, axis=0)

        # Apply preprocessing based on model type
        if "efficientnet" in str(self.model_path).lower():
            image = preprocess_efficientnet(image)

        predictions = self.model.predict(image, verbose=0)
        probs = predictions[0]

        top_indices = np.argsort(probs)[::-1][:top_k]
        results = [(self.class_names[i], float(probs[i])) for i in top_indices]
        return results

    def predict_batch(
        self,
        image_paths: List[Union[str, Path]],
    ) -> List[List[Tuple[str, float]]]:
        """Predict classes for a batch of images.

        Args:
            image_paths: List of image file paths.

        Returns:
            List of prediction results for each image.
        """
        results = []
        for path in image_paths:
            preds = self.predict(path, top_k=1)
            results.append(preds)
        return results

    def get_model_summary(self) -> str:
        """Return model architecture summary as string."""
        from io import StringIO

        stream = StringIO()
        self.model.summary(print_fn=lambda x: stream.write(x + "\n"))
        return stream.getvalue()
