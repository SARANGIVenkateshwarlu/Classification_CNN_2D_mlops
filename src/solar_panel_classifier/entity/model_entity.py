"""Model architecture and configuration entities."""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from enum import Enum


class ModelArchitecture(str, Enum):
    """Supported model architectures."""
    CUSTOM_CNN = "custom"
    MOBILENETV2 = "mobilenetv2"
    EFFICIENTNET_B0 = "efficientnet_b0"
    EFFICIENTNET_B4 = "efficientnet_b4"
    RESNET50 = "resnet50"
    RESNET18 = "resnet18"


class OptimizerName(str, Enum):
    """Supported optimizers."""
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    RMSPROP = "rmsprop"


@dataclass(frozen=True)
class OptimizerConfig:
    """Optimizer hyperparameters."""
    name: OptimizerName = OptimizerName.ADAM
    learning_rate: float = 3e-4
    weight_decay: float = 0.0
    momentum: float = 0.9
    beta_1: float = 0.9
    beta_2: float = 0.999
    epsilon: float = 1e-7
    clipnorm: Optional[float] = None
    clipvalue: Optional[float] = None


@dataclass(frozen=True)
class ModelConfig:
    """Complete model configuration entity."""
    architecture: ModelArchitecture = ModelArchitecture.EFFICIENTNET_B0
    input_shape: tuple = (224, 224, 3)
    num_classes: int = 6
    include_top: bool = False
    weights: str = "imagenet"
    dropout_rate: float = 0.5
    dense_units: List[int] = field(default_factory=lambda: [128])
    dense_activation: str = "relu"
    kernel_regularizer_l2: float = 0.001
    use_batch_norm: bool = True
    use_global_average_pooling: bool = True
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    label_smoothing: float = 0.0
    class_names: List[str] = field(default_factory=lambda: [
        "Bird-drop", "Clean", "Dusty",
        "Electrical-damage", "Physical-Damage", "Snow-Covered"
    ])
