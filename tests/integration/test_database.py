import os
from base64 import b64encode
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import inspect, text

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import create_database_engine
from flexmix_hub.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("FLEXMIX_TEST_MYSQL") != "1",
        reason="Set FLEXMIX_TEST_MYSQL=1 with the dedicated development MySQL running",
    ),
]


def prototype_public_key() -> str:
    return b64encode(
        Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
    ).decode("ascii")


def test_real_mysql_and_alembic():
    """Read-only verification: run alembic upgrade head before this test."""
    engine = create_database_engine(Settings())
    try:
        with engine.connect() as connection:
            version = connection.scalar(text("SELECT VERSION()"))
            assert version.startswith("8.")
            assert connection.scalar(text("SELECT 1")) == 1
            assert connection.scalar(
                text("SELECT version_num FROM alembic_version")
            ) == "0007_backups"
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version", "fleet_mid_allocation", "machine_registry",
            "desired_state_meta", "catalogue_ingredient", "catalogue_drink",
            "catalogue_recipe_action",
            "machine_order_event",
            "machine_command",
            "machine_heartbeat", "backup_metadata",
        }
        command.check(Config("alembic.ini"))
    finally:
        engine.dispose()


def test_app_with_real_mysql():
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/health/ready").json() == {"status": "ok"}


def test_prototype_registry_never_reuses_mid():
    settings = Settings()
    token = settings.prototype_enrollment_token()
    if token is None:
        pytest.skip("Prototype enrollment token is not configured")
    headers = {"X-Flexmix-Prototype-Enrollment-Token": token}
    payload = lambda: {
        "device_uuid": str(uuid4()),
        "device_public_key": prototype_public_key(),
    }
    with TestClient(create_app(settings)) as client:
        first = client.post("/v1/prototype/fleet/machines", json=payload(), headers=headers)
        second = client.post("/v1/prototype/fleet/machines", json=payload(), headers=headers)
        assert first.status_code == 201
        assert second.status_code == 201
        first_mid = first.json()["mid"]
        second_mid = second.json()["mid"]
        assert second_mid == first_mid + 1

        retired = client.post(
            f"/v1/prototype/fleet/machines/{first_mid}/decommission", headers=headers
        )
        assert retired.status_code == 200
        assert retired.json()["status"] == "decommissioned"

        replacement = client.post("/v1/prototype/fleet/machines", json=payload(), headers=headers)
        assert replacement.status_code == 201
        assert replacement.json()["mid"] > second_mid
