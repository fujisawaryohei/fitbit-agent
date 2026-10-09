import importlib
import logging
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.router import router as root_router

_WIRED_MODULES = ["backend.controllers.auth", "backend.controllers.chat"]
_LOCAL_ORIGIN = "http://localhost:3000"


@pytest.fixture
def load_server(container, monkeypatch):
    """server.py を読み込む関数を返す。

    server.py は import 時に新しい Container を作って controllers を wire し直すため、
    テストの後で conftest の session container に wire を戻し、ログフィルターも元に戻す。
    """
    access_logger = logging.getLogger("uvicorn.access")
    original_filters = list(access_logger.filters)
    loaded: list = []

    def _load(cors_origins: str | None = None):
        if cors_origins is None:
            monkeypatch.delenv("CORS_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("CORS_ORIGINS", cors_origins)
        sys.modules.pop("server", None)
        module = importlib.import_module("server")
        loaded.append(module)
        return module

    yield _load

    for module in loaded:
        module.container.unwire()
    container.wire(modules=_WIRED_MODULES)
    for f in list(access_logger.filters):
        if f not in original_filters:
            access_logger.removeFilter(f)
    sys.modules.pop("server", None)


def _paths(routes) -> set[str]:
    return {route.path for route in routes}


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


class TestRouter:
    def test_registers_all_routes(self):
        assert _paths(root_router.routes) >= {
            "/health",
            "/chat",
            "/chats",
            "/chats/{chat_id}/messages",
            "/auth/fitbit",
            "/auth/fitbit/callback",
        }


class TestServerApp:
    def test_app_exposes_router_routes(self, load_server):
        server = load_server()

        assert server.app.title == "Fitbit Agent API"
        assert _paths(server.app.routes) >= _paths(root_router.routes)

    def test_health_endpoint_responds(self, load_server):
        server = load_server()

        response = TestClient(server.app).get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_wires_container_to_controllers(self, load_server):
        server = load_server()
        mock_service = MagicMock()
        mock_service.get_authorization_url.return_value = ("https://www.fitbit.com/auth", "s")

        with server.container.fitbit_service.override(mock_service):
            response = TestClient(server.app, follow_redirects=False).get("/auth/fitbit")

        assert response.status_code in (302, 307)
        assert response.headers["location"] == "https://www.fitbit.com/auth"

    def test_enables_access_log_masking(self, load_server):
        from backend.decorators.masked_credentials import _MaskedCredentialsFilter

        load_server()

        filters = logging.getLogger("uvicorn.access").filters
        assert any(isinstance(f, _MaskedCredentialsFilter) for f in filters)


class TestCors:
    def test_default_allows_only_local_frontend(self, load_server):
        client = TestClient(load_server().app)

        allowed = _preflight(client, _LOCAL_ORIGIN)
        denied = _preflight(client, "https://evil.example")

        assert allowed.headers["access-control-allow-origin"] == _LOCAL_ORIGIN
        assert allowed.headers["access-control-allow-credentials"] == "true"
        assert "access-control-allow-origin" not in denied.headers

    def test_cors_origins_env_is_split_by_comma_and_trimmed(self, load_server):
        client = TestClient(load_server("https://a.example, https://b.example").app)

        for origin in (_LOCAL_ORIGIN, "https://a.example", "https://b.example"):
            assert _preflight(client, origin).headers["access-control-allow-origin"] == origin
        assert "access-control-allow-origin" not in _preflight(client, "https://c.example").headers

    def test_single_cors_origin_env(self, load_server):
        client = TestClient(load_server("https://only.example").app)

        assert (
            _preflight(client, "https://only.example").headers["access-control-allow-origin"]
            == "https://only.example"
        )

    def test_empty_cors_origins_env_keeps_default(self, load_server):
        client = TestClient(load_server("").app)

        assert _preflight(client, _LOCAL_ORIGIN).headers["access-control-allow-origin"] == _LOCAL_ORIGIN
        assert "access-control-allow-origin" not in _preflight(client, "https://a.example").headers
