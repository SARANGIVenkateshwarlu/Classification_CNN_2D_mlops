"""Configuration entities for the MLOps pipeline stages."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass(frozen=True)
class DataIngestionConfig:
    """Configuration for data ingestion stage."""
    root_dir: Path
    source_URL: Optional[str] = None
    local_data_file: Path = Path("artifacts/data_ingestion/data.zip")
    unzip_dir: Path = Path("artifacts/data_ingestion")
    dataset_dir: Path = Path("Data")


@dataclass(frozen=True)
class DataValidationConfig:
    """Configuration for data validation stage."""
    root_dir: Path = Path("artifacts/data_validation")
    status_file: Path = Path("artifacts/data_validation/status.txt")
    required_files: List[str] = field(default_factory=lambda: [
        "Bird-drop", "Clean", "Dusty",
        "Electrical-damage", "Physical-Damage", "Snow-Covered"
    ])
    min_images_per_class: int = 10
    valid_extensions: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


@dataclass(frozen=True)
class DataTransformationConfig:
    """Configuration for data transformation/preprocessing stage."""
    root_dir: Path = Path("artifacts/data_transformation")
    image_size: tuple = (224, 224)
    batch_size: int = 32
    validation_split: float = 0.2
    seed: int = 42
    rescale: bool = True
    normalization_mean: Optional[List[float]] = None
    normalization_std: Optional[List[float]] = None


@dataclass(frozen=True)
class ModelTrainerConfig:
    """Configuration for model training stage."""
    root_dir: Path = Path("artifacts/model_trainer")
    model_name: str = "efficientnet"
    num_classes: int = 6
    epochs: int = 20
    learning_rate: float = 3e-4
    fine_tune_lr: float = 1e-5
    fine_tune_epochs: int = 10
    fine_tune_from_layer: int = 100
    checkpoint_dir: Path = Path("artifacts/model_trainer/checkpoints")
    saved_model_path: Path = Path("artifacts/model_trainer/model.keras")
    use_class_weights: bool = True
    early_stopping_patience: int = 7
    reduce_lr_patience: int = 3


@dataclass(frozen=True)
class ModelEvaluationConfig:
    """Configuration for model evaluation stage."""
    root_dir: Path = Path("artifacts/model_evaluation")
    test_data_path: Path = Path("Data")
    model_path: Path = Path("artifacts/model_trainer/model.keras")
    metric_file_name: Path = Path("artifacts/model_evaluation/metrics.json")
    mlflow_uri: str = "http://localhost:5000"
    all_params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ModelPusherConfig:
    """Configuration for model deployment/pushing stage."""
    root_dir: Path = Path("artifacts/model_pusher")
    model_registry: Path = Path("models")
    model_name: str = "solar_panel_classifier"
    version: str = "v1.0.0"
    s3_bucket: Optional[str] = None
    s3_key_prefix: str = "models/"


@dataclass(frozen=True)
class PipelineConfig:
    """Master pipeline configuration aggregating all stage configs."""
    artifact_dir: Path = Path("artifacts")
    experiment_name: str = "solar_panel_experiment"
    run_name: Optional[str] = None
    data_ingestion: DataIngestionConfig = field(default_factory=DataIngestionConfig)
    data_validation: DataValidationConfig = field(default_factory=DataValidationConfig)
    data_transformation: DataTransformationConfig = field(default_factory=DataTransformationConfig)
    model_trainer: ModelTrainerConfig = field(default_factory=ModelTrainerConfig)
    model_evaluation: ModelEvaluationConfig = field(default_factory=ModelEvaluationConfig)
    model_pusher: ModelPusherConfig = field(default_factory=ModelPusherConfig)
