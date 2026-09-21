import os
from base64 import b64encode
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_hub.main import create_app

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")


def test_command_poll_ack_duplicate_and_wrong_machine():
    settings = Settings(); token = settings.prototype_enrollment_token()
    key_a, key_b = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    uuid_a, uuid_b = uuid4(), uuid4()
    def pub(key): return b64encode(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    def headers(key, uid, method, path): return {"X-Flexmix-Device-Uuid": str(uid), "X-Flexmix-Device-Signature": b64encode(key.sign(request_payload(method, path, uid))).decode()}
    with TestClient(create_app(settings)) as client:
        enroll = {"X-Flexmix-Prototype-Enrollment-Token": token}
        a = client.post("/v1/prototype/fleet/machines", headers=enroll, json={"device_uuid": str(uuid_a), "device_public_key": pub(key_a)}).json()
        b = client.post("/v1/prototype/fleet/machines", headers=enroll, json={"device_uuid": str(uuid_b), "device_public_key": pub(key_b)}).json()
        created = client.post("/v1/prototype/commands", headers=enroll, json={"machine_mid": a["mid"]})
        assert created.status_code == 201
        poll = client.get("/v1/commands/poll", headers=headers(key_a, uuid_a, "GET", "/v1/commands/poll"))
        assert poll.status_code == 200 and len(poll.json()["commands"]) == 1
        command = poll.json()["commands"][0]
        wrong = client.post("/v1/commands/ack", headers=headers(key_b, uuid_b, "POST", "/v1/commands/ack"), json={"command_id": command["command_id"], "status": "acknowledged"})
        assert wrong.status_code == 404
        ack_headers = headers(key_a, uuid_a, "POST", "/v1/commands/ack")
        assert client.post("/v1/commands/ack", headers=ack_headers, json={"command_id": command["command_id"], "status": "acknowledged"}).status_code == 200
        assert client.post("/v1/commands/ack", headers=ack_headers, json={"command_id": command["command_id"], "status": "acknowledged"}).status_code == 200
