from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from flexmix_hub.main import create_app


def test_startup_liveness_shutdown_without_database(settings, monkeypatch):
    engine = MagicMock()
    monkeypatch.setattr("flexmix_hub.main.create_database_engine", lambda _: engine)
    app = create_app(settings)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        engine.connect.assert_not_called()
        assert client.get("/v1/state").status_code == 401
        assert client.get("/docs").status_code == 404
        engine.dispose.assert_not_called()
    engine.dispose.assert_called_once()


@pytest.mark.parametrize("database_available", [True, False])
def test_readiness_handles_database_failure(settings, monkeypatch, database_available):
    engine = MagicMock()
    if not database_available:
        engine.connect.side_effect = OperationalError(
            "SELECT 1", {}, Exception("sensitive-driver-details")
        )
    monkeypatch.setattr("flexmix_hub.main.create_database_engine", lambda _: engine)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
        assert response.status_code == (200 if database_available else 503)
        assert response.json() == {
            "status": "ok" if database_available else "unavailable"
        }
        assert "sensitive-driver-details" not in response.text
        assert client.get("/health").status_code == 200
