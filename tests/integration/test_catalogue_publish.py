import os
from base64 import b64encode
from uuid import uuid4
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from flexmix_hub.config import Settings
from flexmix_hub.main import create_app
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_machine.desired_state import LocalDesiredState

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")

def test_publish_snapshot_apply_twice(tmp_path):
    settings = Settings(); token = settings.prototype_enrollment_token(); key = Ed25519PrivateKey.generate(); uid = uuid4()
    pub = b64encode(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    auth = {"X-Flexmix-Prototype-Enrollment-Token": token}
    with TestClient(create_app(settings)) as client:
        reg = client.post("/v1/prototype/fleet/machines", headers=auth, json={"device_uuid": str(uid), "device_public_key": pub})
        assert reg.status_code == 201
        payload = {"ingredients": [{"id": "water", "name": "Water", "kind": "PUMP"}], "drinks": [{"id": "tea", "name": "Tea", "price_cents": 100, "published": True, "recipe": [{"ingredient_id": "water", "amount_grams": 10}]}]}
        published = client.put("/v1/prototype/catalogue", headers=auth, json=payload)
        assert published.status_code == 200
        machine_headers = {"X-Flexmix-Device-Uuid": str(uid), "X-Flexmix-Device-Signature": b64encode(key.sign(request_payload("GET", "/v1/state", uid))).decode()}
        snapshot = client.get("/v1/state", headers=machine_headers).json()
        local = LocalDesiredState(tmp_path / "state.json", mid=reg.json()["mid"], available_ingredient_ids={"water"})
        assert local.apply(snapshot) == local.apply(snapshot)
        assert local.load()["drinks"][0]["id"] == "tea"
