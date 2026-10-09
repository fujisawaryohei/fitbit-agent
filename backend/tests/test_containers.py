from unittest.mock import MagicMock, patch

import pytest

from backend import containers


class TestCreateConn:
    def test_yields_connection_then_releases_it(self):
        conn = MagicMock()
        with patch.object(containers, "get_connection", return_value=conn), \
             patch.object(containers, "release_connection") as release:
            gen = containers._create_conn()
            assert next(gen) is conn
            release.assert_not_called()
            gen.close()

        release.assert_called_once_with(conn)

    def test_releases_connection_when_consumer_raises(self):
        conn = MagicMock()
        with patch.object(containers, "get_connection", return_value=conn), \
             patch.object(containers, "release_connection") as release:
            gen = containers._create_conn()
            next(gen)
            with pytest.raises(RuntimeError):
                gen.throw(RuntimeError("boom"))

        release.assert_called_once_with(conn)


class TestCreateFitbitClient:
    def test_reads_credentials_from_env(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "id-1")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "secret-1")
        monkeypatch.setenv("FITBIT_REDIRECT_URI", "https://example.com/cb")

        client = containers._create_fitbit_client()

        assert client._client_id == "id-1"
        assert client._client_secret == "secret-1"
        assert client._redirect_uri == "https://example.com/cb"

    def test_falls_back_to_defaults_when_env_missing(self, monkeypatch):
        for name in ("FITBIT_CLIENT_ID", "FITBIT_CLIENT_SECRET", "FITBIT_REDIRECT_URI"):
            monkeypatch.delenv(name, raising=False)

        client = containers._create_fitbit_client()

        assert client._client_id == ""
        assert client._client_secret == ""
        assert client._redirect_uri == "http://localhost:8000/auth/fitbit/callback"
