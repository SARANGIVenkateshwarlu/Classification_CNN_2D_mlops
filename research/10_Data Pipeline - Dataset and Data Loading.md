
# 10. Data Pipeline - Dataset and Data Loading
data_pipeline = """\"\"\"
Data Pipeline for Image Classification
Features: Augmentation, validation, versioning with DVC
\"\"\"

import os
import json
from pathlib import Path
from typing import Optional, Tuple, List, Callable, Union
import logging

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import albumentations as A
from albumentations.pytorch import ToTensorV2
import cv2

logger = logging.getLogger(__name__)


class ImageClassificationDataset(Dataset):
    \"\"\"Custom Dataset for Image Classification\"\"\"
    
    def __init__(
        self,
        data_dir: Union[str, Path],
        annotations_file: Optional[str] = None,
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
        class_names: Optional[List[str]] = None,
        mode: str = "train"
    ):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.target_transform = target_transform
        self.mode = mode
        
        # Load annotations
        if annotations_file and Path(annotations_file).exists():
            self.annotations = pd.read_csv(annotations_file)
        else:
            # Auto-discover images
            self.annotations = self._discover_images()
        
        # Setup class names
        if class_names:
            self.class_names = class_names
        else:
            self.class_names = sorted(self.annotations['label'].unique().tolist())
        
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.class_names)}
        self.num_classes = len(self.class_names)
        
        logger.info(f"Loaded {len(self.annotations)} images from {data_dir}")
        logger.info(f"Classes: {self.num_classes}")
    
    def _discover_images(self) -> pd.DataFrame:
        \"\"\"Auto-discover images in directory structure\"\"\"
        data = []
        
        # Assume directory structure: data_dir/class_name/image.jpg
        for class_dir in sorted(self.data_dir.iterdir()):
            if class_dir.is_dir():
                label = class_dir.name
                for img_path in class_dir.glob("*"):
                    if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                        data.append({
                            'image_path': str(img_path),
                            'label': label,
                            'filename': img_path.name
                        })
        
        return pd.DataFrame(data)
    
    def __len__(self) -> int:
        return len(self.annotations)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        row = self.annotations.iloc[idx]
        img_path = row['image_path']
        label = self.class_to_idx[row['label']]
        
        # Load image
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {e}")
            # Return a blank image
            image = Image.new('RGB', (224, 224), color='black')
        
        # Apply transforms
        if self.transform:
            if isinstance(self.transform, A.Compose):
                # Albumentations transform
                image_np = np.array(image)
                transformed = self.transform(image=image_np)
                image = transformed['image']
            else:
                # Torchvision transform
                image = self.transform(image)
        
        if self.target_transform:
            label = self.target_transform(label)
        
        return image, label
    
    def get_class_distribution(self) -> pd.Series:
        \"\"\"Get distribution of classes\"\"\"
        return self.annotations['label'].value_counts()


def get_train_transforms(img_size: int = 224, augment: bool = True) -> Callable:
    \"\"\"Get training transforms with augmentation\"\"\"
    if augment:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.RandomRotate90(p=0.3),
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.2,
                rotate_limit=30,
                p=0.5
            ),
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5
            ),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=0.3
            ),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.Blur(blur_limit=3, p=0.2),
            A.CoarseDropout(
                max_holes=8,
                max_height=img_size//8,
                max_width=img_size//8,
                min_holes=1,
                p=0.3
            ),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ToTensorV2()
        ])
    else:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ToTensorV2()
        ])


def get_val_transforms(img_size: int = 224) -> Callable:
    \"\"\"Get validation transforms\"\"\"
    return A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
        ToTensorV2()
    ])


def get_test_transforms(img_size: int = 224) -> Callable:
    \"\"\"Get test transforms with TTA\"\"\"
    return A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
        ToTensorV2()
    ])


def create_data_loaders(
    train_dir: str,
    val_dir: str,
    test_dir: Optional[str] = None,
    batch_size: int = 32,
    num_workers: int = 4,
    img_size: int = 224,
    pin_memory: bool = True
) -> Tuple[DataLoader, DataLoader, Optional[DataLoader]]:
    \"\"\"Create train, validation, and test data loaders\"\"\"
    
    # Create datasets
    train_dataset = ImageClassificationDataset(
        train_dir,
        transform=get_train_transforms(img_size, augment=True),
        mode="train"
    )
    
    val_dataset = ImageClassificationDataset(
        val_dir,
        transform=get_val_transforms(img_size),
        class_names=train_dataset.class_names,
        mode="val"
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True,
        persistent_workers=True if num_workers > 0 else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=True if num_workers > 0 else False
    )
    
    test_loader = None
    if test_dir and Path(test_dir).exists():
        test_dataset = ImageClassificationDataset(
            test_dir,
            transform=get_test_transforms(img_size),
            class_names=train_dataset.class_names,
            mode="test"
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory
        )
    
    return train_loader, val_loader, test_loader


def split_dataset(
    data_dir: str,
    output_dir: str,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
):
    \"\"\"Split dataset into train/val/test sets\"\"\"
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    
    # Collect all images
    all_images = []
    for class_dir in sorted(data_dir.iterdir()):
        if class_dir.is_dir():
            label = class_dir.name
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    all_images.append((str(img_path), label))
    
    df = pd.DataFrame(all_images, columns=['image_path', 'label'])
    
    # Stratified split
    train_df, temp_df = train_test_split(
        df, 
        test_size=(val_ratio + test_ratio),
        stratify=df['label'],
        random_state=seed
    )
    
    val_df, test_df = train_test_split(
        temp_df,
        test_size=test_ratio / (val_ratio + test_ratio),
        stratify=temp_df['label'],
        random_state=seed
    )
    
    # Copy files to new directories
    splits = {'train': train_df, 'val': val_df, 'test': test_df}
    
    for split_name, split_df in splits.items():
        split_dir = output_dir / split_name
        
        for _, row in split_df.iterrows():
            src_path = Path(row['image_path'])
            dst_dir = split_dir / row['label']
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / src_path.name
            
            # Copy or symlink
            if not dst_path.exists():
                dst_path.symlink_to(src_path.resolve())
    
    logger.info(f"Dataset split complete:")
    logger.info(f"  Train: {len(train_df)}")
    logger.info(f"  Val: {len(val_df)}")
    logger.info(f"  Test: {len(test_df)}")
    
    return output_dir


class DataValidator:
    \"\"\"Validate data quality and schema\"\"\"
    
    @staticmethod
    def validate_image(file_path: str) -> bool:
        \"\"\"Validate image file\"\"\"
        try:
            img = Image.open(file_path)
            img.verify()
            return True
        except Exception as e:
            logger.warning(f"Invalid image {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_dataset(data_dir: str) -> dict:
        \"\"\"Validate entire dataset\"\"\"
        data_dir = Path(data_dir)
        stats = {
            'total_images': 0,
            'invalid_images': 0,
            'classes': {},
            'issues': []
        }
        
        for class_dir in sorted(data_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            
            class_name = class_dir.name
            class_images = 0
            
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    stats['total_images'] += 1
                    class_images += 1
                    
                    if not DataValidator.validate_image(str(img_path)):
                        stats['invalid_images'] += 1
                        stats['issues'].append(f"Invalid: {img_path}")
            
            stats['classes'][class_name] = class_images
        
        return stats


if __name__ == "__main__":
    # Example usage
    stats = DataValidator.validate_dataset("data/train")
    print(json.dumps(stats, indent=2))
"""

with open(f"{project_root}/src/data/dataset.py", "w") as f:
    f.write(data_pipeline)

print("✅ Data pipeline created")
