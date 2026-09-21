import os
from base64 import b64encode
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from flexmix_hub.api.machine import SELF_PATH
from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_hub.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("FLEXMIX_TEST_MYSQL") != "1",
        reason="Set FLEXMIX_TEST_MYSQL=1 with the dedicated development MySQL running",
    ),
]


def public_key(private_key: Ed25519PrivateKey) -> str:
    return b64encode(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
    ).decode("ascii")


def auth_headers(private_key: Ed25519PrivateKey, device_uuid: UUID) -> dict[str, str]:
    signature = private_key.sign(request_payload("GET", SELF_PATH, device_uuid))
    return {
        "X-Flexmix-Device-Uuid": str(device_uuid),
        "X-Flexmix-Device-Signature": b64encode(signature).decode("ascii"),
    }


def test_machine_self_requires_registered_active_identity():
    settings = Settings()
    enrollment_token = settings.prototype_enrollment_token()
    if enrollment_token is None:
        pytest.skip("Prototype enrollment token is not configured")
    enrollment_headers = {"X-Flexmix-Prototype-Enrollment-Token": enrollment_token}

    first_key, second_key, unknown_key = (
        Ed25519PrivateKey.generate(),
        Ed25519PrivateKey.generate(),
        Ed25519PrivateKey.generate(),
    )
    first_uuid, second_uuid, unknown_uuid = uuid4(), uuid4(), uuid4()

    with TestClient(create_app(settings)) as client:
        first = client.post(
            "/v1/prototype/fleet/machines",
            headers=enrollment_headers,
            json={"device_uuid": str(first_uuid), "device_public_key": public_key(first_key)},
        )
        second = client.post(
            "/v1/prototype/fleet/machines",
            headers=enrollment_headers,
            json={"device_uuid": str(second_uuid), "device_public_key": public_key(second_key)},
        )
        assert first.status_code == 201
        assert second.status_code == 201

        own_state = client.get(SELF_PATH, headers=auth_headers(first_key, first_uuid))
        assert own_state.status_code == 200
        assert own_state.json()["mid"] == first.json()["mid"]
        assert own_state.json()["device_uuid"] == str(first_uuid)

        bad_signature = client.get(
            SELF_PATH,
            headers={
                "X-Flexmix-Device-Uuid": str(first_uuid),
                "X-Flexmix-Device-Signature": b64encode(b"invalid").decode("ascii"),
            },
        )
        assert bad_signature.status_code == 401

        unknown = client.get(SELF_PATH, headers=auth_headers(unknown_key, unknown_uuid))
        assert unknown.status_code == 401

        # The UUID is selected by the caller but the key must prove that exact identity.
        impersonation = client.get(SELF_PATH, headers=auth_headers(first_key, second_uuid))
        assert impersonation.status_code == 401

        retired = client.post(
            f"/v1/prototype/fleet/machines/{first.json()['mid']}/decommission",
            headers=enrollment_headers,
        )
        assert retired.status_code == 200
        assert client.get(SELF_PATH, headers=auth_headers(first_key, first_uuid)).status_code == 403
