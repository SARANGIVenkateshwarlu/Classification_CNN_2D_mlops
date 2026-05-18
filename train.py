"""
Solar Panel Image Classification - Training Script
==================================================
Reproducible training pipeline for CNN-based solar panel classifiers.

Supports:
    - Custom CNN (from scratch)
    - MobileNetV2 (transfer learning)
    - EfficientNetB0 (transfer learning + hyperparameter tuning)

Usage:
    python train.py --model efficientnet --epochs 20
    python train.py --model mobilenetv2 --epochs 20
    python train.py --model custom --epochs 50
"""

import argparse
import os
from pathlib import Path

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import MobileNetV2, EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input

from src.solar_panel_classifier.config import (
    DATA_DIR,
    MODELS_DIR,
    IMG_SIZE,
    BATCH_SIZE,
    SEED,
    VALIDATION_SPLIT,
    NUM_CLASSES,
    CLASS_NAMES,
)
from src.solar_panel_classifier.data_loader import create_data_augmentation, get_class_weights


def build_custom_cnn(input_shape=(224, 224, 3), num_classes=6) -> models.Sequential:
    """Build a custom CNN with regularization for solar panel classification."""
    data_augmentation = create_data_augmentation()

    model = models.Sequential([
        layers.Input(shape=input_shape),
        data_augmentation,
        layers.Rescaling(1.0 / 255),

        # Conv Block 1
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Conv Block 2
        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Conv Block 3
        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.35),

        # Classifier
        layers.Flatten(),
        layers.Dense(256, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(128, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=optimizers.Adam(learning_rate=3e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def build_mobilenetv2(input_shape=(224, 224, 3), num_classes=6) -> models.Sequential:
    """Build MobileNetV2-based transfer learning model."""
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    data_augmentation = create_data_augmentation()

    model = models.Sequential([
        layers.Input(shape=input_shape),
        data_augmentation,
        layers.Rescaling(1.0 / 255),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def build_efficientnet(input_shape=(224, 224, 3), num_classes=6) -> models.Sequential:
    """Build EfficientNetB0-based transfer learning model."""
    base_model = EfficientNetB0(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    data_augmentation = create_data_augmentation()

    model = models.Sequential([
        layers.Input(shape=input_shape),
        data_augmentation,
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train(
    model_type: str = "efficientnet",
    epochs: int = 20,
    save_name: str = "solar_panel_classifier",
):
    """Train a model and save it."""
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    print(f"Loading dataset from: {DATA_DIR}")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=VALIDATION_SPLIT,
        subset="training",
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        seed=SEED,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=VALIDATION_SPLIT,
        subset="validation",
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        seed=SEED,
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Classes: {class_names}")

    # Compute class weights for imbalance
    class_weights = get_class_weights(DATA_DIR)
    print(f"Class weights: {class_weights}")

    # Build model
    if model_type == "custom":
        model = build_custom_cnn(num_classes=num_classes)
    elif model_type == "mobilenetv2":
        model = build_mobilenetv2(num_classes=num_classes)
    elif model_type == "efficientnet":
        model = build_efficientnet(num_classes=num_classes)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    model.summary()

    # Callbacks
    early_stop = callbacks.EarlyStopping(
        monitor="val_loss",
        patience=7,
        restore_best_weights=True,
        verbose=1,
    )
    reduce_lr = callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=1e-7,
        verbose=1,
    )

    # Train
    print(f"\nTraining {model_type} for up to {epochs} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=[early_stop, reduce_lr],
        class_weight=class_weights,
    )

    # Evaluate
    val_loss, val_acc = model.evaluate(val_ds, verbose=0)
    print(f"\nFinal validation accuracy: {val_acc:.4f}")
    print(f"Final validation loss: {val_loss:.4f}")

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    keras_path = MODELS_DIR / f"{save_name}.keras"
    h5_path = MODELS_DIR / f"{save_name}.h5"

    model.save(str(keras_path))
    print(f"Saved model (Keras): {keras_path}")

    try:
        model.save(str(h5_path))
        print(f"Saved model (HDF5):  {h5_path}")
    except Exception as e:
        print(f"HDF5 save skipped: {e}")

    return model, history


def main():
    parser = argparse.ArgumentParser(description="Train Solar Panel Classifier")
    parser.add_argument(
        "--model",
        type=str,
        default="efficientnet",
        choices=["custom", "mobilenetv2", "efficientnet"],
        help="Model architecture",
    )
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--save-name", type=str, default="solar_panel_classifier", help="Output filename")
    args = parser.parse_args()

    train(args.model, args.epochs, args.save_name)


if __name__ == "__main__":
    main()
