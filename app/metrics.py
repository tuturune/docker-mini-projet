"""Métriques exposées au format Prometheus sur /metrics."""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Nombre de requêtes HTTP",
    ["method", "route", "status"],
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Durée de traitement des requêtes HTTP",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
PREDICTIONS = Counter(
    "predictions_total",
    "Nombre de prédictions par version du modèle et par sentiment",
    ["model_version", "label"],
)
PREDICTION_CONFIDENCE = Histogram(
    "prediction_confidence",
    "Score de confiance des prédictions",
    ["model_version"],
    buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0),
)
MODEL_INFO = Gauge(
    "model_info",
    "Modèle chargé (valeur 1) avec sa version et sa précision mesurée",
    ["model_version", "accuracy"],
)
