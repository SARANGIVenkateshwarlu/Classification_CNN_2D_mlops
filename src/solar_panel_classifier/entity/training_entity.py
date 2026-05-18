"""Training and data augmentation configuration entities."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class AugmentationConfig:
    """Data augmentation pipeline configuration."""
    enabled: bool = True
    random_flip_mode: str = "horizontal"
    rotation_factor: float = 0.15
    zoom_factor: float = 0.15
    contrast_factor: float = 0.0
    brightness_factor: float = 0.0
    shear_factor: float = 0.0
    fill_mode: str = "nearest"


@dataclass(frozen=True)
class CallbackConfig:
    """Training callbacks configuration."""
    early_stopping_enabled: bool = True
    early_stopping_monitor: str = "val_loss"
    early_stopping_patience: int = 7
    early_stopping_restore_best_weights: bool = True
    reduce_lr_enabled: bool = True
    reduce_lr_monitor: str = "val_loss"
    reduce_lr_factor: float = 0.5
    reduce_lr_patience: int = 3
    reduce_lr_min_lr: float = 1e-7
    model_checkpoint_enabled: bool = True
    model_checkpoint_monitor: str = "val_accuracy"
    model_checkpoint_save_best_only: bool = True
    tensorboard_enabled: bool = False
    tensorboard_log_dir: Optional[str] = None
    learning_rate_scheduler: Optional[str] = None  # "cosine", "exponential", "step"


@dataclass(frozen=True)
class TrainingConfig:
    """Complete training configuration entity."""
    epochs: int = 20
    batch_size: int = 32
    validation_split: float = 0.2
    seed: int = 42
    use_mixed_precision: bool = False
    use_gradient_clipping: bool = False
    gradient_clip_norm: float = 1.0
    use_class_weights: bool = True
    shuffle: bool = True
    verbose: int = 1
    workers: int = 4
    use_multiprocessing: bool = False
    prefetch_buffer_size: int = 2
    augmentation: AugmentationConfig = field(default_factory=AugmentationConfig)
    callbacks: CallbackConfig = field(default_factory=CallbackConfig)
