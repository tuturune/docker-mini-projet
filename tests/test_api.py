import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("MODEL_VERSION", "v1")
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_version": "v1", "database": "up"}


def test_live_does_not_depend_on_database(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Un chef-d'œuvre, des acteurs brillants et une histoire magnifique.", "positif"),
        ("Un film ennuyeux et mal joué, une perte de temps totale.", "negatif"),
    ],
)
def test_predict(client, text, expected):
    response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == expected
    assert 0.5 <= body["confidence"] <= 1
    assert body["model_version"] == "v1"


def test_predict_rejects_empty_text(client):
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422


def test_history_records_predictions(client):
    client.post("/predict", json={"text": "Superbe film, je recommande."})
    history = client.get("/history?limit=5").json()
    assert len(history) == 1
    assert history[0]["text"] == "Superbe film, je recommande."


def test_metrics(client):
    client.post("/predict", json={"text": "Superbe film, je recommande."})
    body = client.get("/metrics").text
    assert "predictions_total" in body
    assert "http_request_duration_seconds" in body
    assert "model_info{accuracy=" in body


def test_simulated_errors(client, monkeypatch):
    monkeypatch.setenv("FAULT_ERROR_RATE", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with TestClient(app) as c:
        response = c.post("/predict", json={"text": "Superbe film, je recommande."})
    assert response.status_code == 500
