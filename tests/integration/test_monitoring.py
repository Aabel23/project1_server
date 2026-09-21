import os
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import update

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import create_database_engine, create_session_factory
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_hub.main import create_app
from flexmix_hub.modules.monitoring.models import MachineHeartbeat

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")


def test_heartbeat_identity_and_stale_status():
    settings = Settings(); token = settings.prototype_enrollment_token()
    key_a, key_b = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    uid_a, uid_b = uuid4(), uuid4()
    def pub(k): return b64encode(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    def headers(k, uid): return {"X-Flexmix-Device-Uuid": str(uid), "X-Flexmix-Device-Signature": b64encode(k.sign(request_payload("POST", "/v1/beat", uid))).decode()}
    with TestClient(create_app(settings)) as client:
        enroll = {"X-Flexmix-Prototype-Enrollment-Token": token}
        a = client.post("/v1/prototype/fleet/machines", headers=enroll, json={"device_uuid": str(uid_a), "device_public_key": pub(key_a)}).json()
        client.post("/v1/prototype/fleet/machines", headers=enroll, json={"device_uuid": str(uid_b), "device_public_key": pub(key_b)})
        heartbeat = {"reported_at": datetime.now(timezone.utc).isoformat(), "status": "ready", "schema_version": "machine-v1", "selling_available": True}
        assert client.post("/v1/beat", headers=headers(key_a, uid_a), json=heartbeat).status_code == 200
        assert client.get(f"/v1/prototype/monitoring/machines/{a['mid']}").json()["online"] is True
        assert client.post("/v1/beat", headers=headers(key_a, uid_b), json=heartbeat).status_code == 401
        engine = create_database_engine(settings)
        try:
            with create_session_factory(engine)() as session:
                session.execute(update(MachineHeartbeat).where(MachineHeartbeat.machine_mid == a["mid"]).values(received_at=datetime.now(timezone.utc) - timedelta(seconds=121)))
                session.commit()
        finally:
            engine.dispose()
        assert client.get(f"/v1/prototype/monitoring/machines/{a['mid']}").json()["online"] is False
