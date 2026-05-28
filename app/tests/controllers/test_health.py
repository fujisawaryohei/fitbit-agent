from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers.health import router as health_router

_app = FastAPI()
_app.include_router(health_router)


def test_health_returns_ok():
    client = TestClient(_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
