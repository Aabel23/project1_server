import os
from base64 import b64encode
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from flexmix_hub.modules.fleet.models import MachineRegistry

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import create_database_engine, create_session_factory
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_hub.main import create_app
from flexmix_hub.modules.events.models import MachineOrderEvent

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")


def test_event_batch_is_idempotent_and_acks_cursor():
    settings = Settings()
    token = settings.prototype_enrollment_token()
    key = Ed25519PrivateKey.generate()
    device_uuid = uuid4()
    public = b64encode(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    with TestClient(create_app(settings)) as client:
        registered = client.post("/v1/prototype/fleet/machines", headers={"X-Flexmix-Prototype-Enrollment-Token": token}, json={"device_uuid": str(device_uuid), "device_public_key": public})
        assert registered.status_code == 201
        event = {"event_id": str(uuid4()), "cursor": 1, "serial": "S-1", "status": "used", "drink_id": "latte", "price_cents": 350, "occurred_at": "2026-09-17T10:00:00Z"}
        batch = {"cursor_from": 0, "cursor_to": 1, "rows": [event]}
        headers = {"X-Flexmix-Device-Uuid": str(device_uuid), "X-Flexmix-Device-Signature": b64encode(key.sign(request_payload("POST", "/v1/events", device_uuid))).decode()}
        first = client.post("/v1/events", headers=headers, json=batch)
        second = client.post("/v1/events", headers=headers, json=batch)
        assert first.json() == {"ack": "ok", "cursor_to": 1}
        assert second.json() == {"ack": "ok", "cursor_to": 1}
    engine = create_database_engine(settings)
    try:
        with create_session_factory(engine)() as session:
            mid = registered.json()["mid"]
            assert session.scalar(select(func.count()).select_from(MachineOrderEvent).where(MachineOrderEvent.machine_mid == mid)) == 1
    finally:
        engine.dispose()
