"""
Solar Panel Image Classification - CLI Entry Point
==================================================
Command-line tool for batch or single-image inference.

Usage:
    python main.py predict --image path/to/image.jpg
    python main.py predict --image path/to/image.jpg --model efficientnet --top-k 3
    python main.py info
    python main.py batch --dir path/to/images/
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.solar_panel_classifier.predictor import SolarPanelClassifier
from src.solar_panel_classifier.config import CLASS_NAMES, DEFAULT_MODEL_PATH


def predict_single(image_path: str, model_name: Optional[str], top_k: int):
    """Run inference on a single image."""
    if model_name:
        classifier = SolarPanelClassifier(model_name=model_name)
    else:
        classifier = SolarPanelClassifier()

    print(f"\nPredicting: {image_path}")
    print("-" * 40)

    results = classifier.predict(image_path, top_k=top_k)

    for rank, (cls, conf) in enumerate(results, 1):
        bar = "#" * int(conf * 20)
        print(f"  {rank}. {cls:<20} {conf:.2%} {bar}")

    top_class, top_conf = results[0]
    print("-" * 40)
    print(f"Result: {top_class} ({top_conf:.2%})")


def predict_batch(image_dir: str, model_name: Optional[str]):
    """Run inference on all images in a directory."""
    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"Error: Directory not found: {image_dir}")
        sys.exit(1)

    image_paths = []
    seen = set()
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
        for p in image_dir.glob(ext):
            if p not in seen:
                image_paths.append(p)
                seen.add(p)

    if not image_paths:
        print(f"No images found in {image_dir}")
        sys.exit(1)

    if model_name:
        classifier = SolarPanelClassifier(model_name=model_name)
    else:
        classifier = SolarPanelClassifier()

    print(f"\nBatch prediction on {len(image_paths)} images")
    print("=" * 60)

    for path in sorted(image_paths):
        results = classifier.predict(str(path), top_k=1)
        cls, conf = results[0]
        print(f"  {path.name:<30} -> {cls:<20} ({conf:.2%})")


def show_info(model_name: Optional[str]):
    """Display model information."""
    if model_name:
        classifier = SolarPanelClassifier(model_name=model_name)
    else:
        classifier = SolarPanelClassifier()

    print("\n" + "=" * 60)
    print("  Solar Panel Classifier - Model Information")
    print("=" * 60)
    print(f"  Model path: {classifier.model_path}")
    print(f"  Classes ({classifier.num_classes}):")
    for i, name in enumerate(classifier.class_names):
        print(f"    {i}. {name}")
    print("\n" + classifier.get_model_summary())


def main():
    parser = argparse.ArgumentParser(
        prog="solar-panel-classifier",
        description="CLI for Solar Panel Image Classification",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Predict single image
    pred_parser = subparsers.add_parser("predict", help="Predict a single image")
    pred_parser.add_argument("--image", "-i", required=True, help="Path to image file")
    pred_parser.add_argument(
        "--model", "-m", default=None, help="Model name ('efficientnet' or 'mobilenetv2')"
    )
    pred_parser.add_argument(
        "--top-k", "-k", type=int, default=1, help="Number of top predictions to show"
    )

    # Batch prediction
    batch_parser = subparsers.add_parser("batch", help="Predict all images in a directory")
    batch_parser.add_argument("--dir", "-d", required=True, help="Directory containing images")
    batch_parser.add_argument(
        "--model", "-m", default=None, help="Model name ('efficientnet' or 'mobilenetv2')"
    )

    # Model info
    info_parser = subparsers.add_parser("info", help="Show model information")
    info_parser.add_argument(
        "--model", "-m", default=None, help="Model name ('efficientnet' or 'mobilenetv2')"
    )

    args = parser.parse_args()

    if args.command == "predict":
        predict_single(args.image, args.model, args.top_k)
    elif args.command == "batch":
        predict_batch(args.dir, args.model)
    elif args.command == "info":
        show_info(args.model)


if __name__ == "__main__":
    main()
