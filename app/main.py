"""API d'analyse de sentiment d'avis de films en français."""

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import Database, PredictionRecord
from app.metrics import (
    HTTP_LATENCY,
    HTTP_REQUESTS,
    MODEL_INFO,
    PREDICTION_CONFIDENCE,
    PREDICTIONS,
)
from app.model import SentimentModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sentiment-api")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.model = SentimentModel(settings.models_dir, settings.model_version)
    app.state.db = Database(settings.database_url)
    app.state.db.init_schema()
    MODEL_INFO.labels(app.state.model.version, str(app.state.model.accuracy)).set(1)
    logger.info("Modèle %s chargé (précision %.4f)", app.state.model.version, app.state.model.accuracy)
    yield


app = FastAPI(title="API d'analyse de sentiment", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = route.path if route else "inconnue"
        if path != "/metrics":
            HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
            HTTP_REQUESTS.labels(request.method, path, str(status)).inc()


class PredictIn(BaseModel):
    text: str = Field(min_length=3, max_length=5000, examples=["Un film magnifique, je recommande !"])


class PredictOut(BaseModel):
    label: str
    confidence: float
    model_version: str


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/predict", response_model=PredictOut)
async def predict(payload: PredictIn, request: Request) -> PredictOut:
    settings = request.app.state.settings
    # Pannes simulées, réglables par variables d'environnement, pour tester la supervision.
    if settings.fault_latency_ms:
        await asyncio.sleep(settings.fault_latency_ms / 1000)
    if settings.fault_error_rate and random.random() < settings.fault_error_rate:
        raise HTTPException(status_code=500, detail="Erreur simulée")

    model = request.app.state.model
    prediction = model.predict(payload.text)
    PREDICTIONS.labels(model.version, prediction.label).inc()
    PREDICTION_CONFIDENCE.labels(model.version).observe(prediction.confidence)

    try:
        request.app.state.db.save(
            PredictionRecord(
                text=payload.text,
                label=prediction.label,
                confidence=prediction.confidence,
                model_version=model.version,
            )
        )
    except Exception as exc:
        logger.exception("Impossible d'enregistrer la prédiction")
        raise HTTPException(status_code=503, detail="Base de données indisponible") from exc

    return PredictOut(label=prediction.label, confidence=prediction.confidence, model_version=model.version)


@app.get("/history")
def history(request: Request, limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    records = request.app.state.db.latest(limit)
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "text": r.text,
            "label": r.label,
            "confidence": r.confidence,
            "model_version": r.model_version,
        }
        for r in records
    ]


@app.get("/health")
def health(request: Request) -> JSONResponse:
    db_up = request.app.state.db.is_up()
    body = {
        "status": "ok" if db_up else "degraded",
        "model_version": request.app.state.model.version,
        "database": "up" if db_up else "down",
    }
    return JSONResponse(body, status_code=200 if db_up else 503)


@app.get("/health/live")
def live() -> dict:
    """Répond tant que le processus tourne, sans vérifier la base."""
    return {"status": "alive"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
