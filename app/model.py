"""Chargement du modèle et prédiction."""

from dataclasses import dataclass
from pathlib import Path

import joblib


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float


class SentimentModel:
    def __init__(self, models_dir: Path, version: str):
        path = models_dir / f"sentiment-{version}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Modèle introuvable : {path}")
        artifact = joblib.load(path)
        self.version: str = artifact["version"]
        self.accuracy: float = artifact["accuracy"]
        self._pipeline = artifact["pipeline"]
        self._labels: dict[int, str] = artifact["labels"]

    def predict(self, text: str) -> Prediction:
        probas = self._pipeline.predict_proba([text])[0]
        best = int(probas.argmax())
        label = self._labels[int(self._pipeline.classes_[best])]
        return Prediction(label=label, confidence=round(float(probas[best]), 4))
