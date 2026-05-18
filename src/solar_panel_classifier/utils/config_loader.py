"""Configuration loader supporting YAML and environment variables."""

import os
from pathlib import Path
from typing import Any, Dict, Optional


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with env overrides."""
    if config_path is None:
        config_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "config"
            / "config.yaml"
        )

    config = {}
    if config_path.exists():
        try:
            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
        except ImportError:
            pass

    config["env"] = {
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "api_port": int(os.getenv("API_PORT", "8000")),
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "model_path": os.getenv("MODEL_PATH"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }

    return config
