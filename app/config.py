"""Configuration lue depuis les variables d'environnement."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model_version: str
    models_dir: Path
    database_url: str
    fault_error_rate: float
    fault_latency_ms: int


def get_settings() -> Settings:
    return Settings(
        model_version=os.getenv("MODEL_VERSION", "v1"),
        models_dir=Path(os.getenv("MODELS_DIR", "models")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./predictions.db"),
        fault_error_rate=float(os.getenv("FAULT_ERROR_RATE", "0")),
        fault_latency_ms=int(os.getenv("FAULT_LATENCY_MS", "0")),
    )
