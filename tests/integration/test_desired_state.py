import os
from base64 import b64encode
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import select

from flexmix_hub.config import Settings
from flexmix_hub.infrastructure.database.session import create_database_engine, create_session_factory
from flexmix_hub.infrastructure.security.device_identity import request_payload
from flexmix_hub.main import create_app
from flexmix_hub.modules.catalogue.service import DrinkDraft, IngredientDraft, RecipeActionDraft, replace_catalogue

pytestmark = pytest.mark.skipif(
    os.environ.get("FLEXMIX_TEST_MYSQL") != "1",
    reason="Set FLEXMIX_TEST_MYSQL=1 with the dedicated development MySQL running",
)


def key_text(key: Ed25519PrivateKey) -> str:
    return b64encode(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )).decode("ascii")


def test_snapshot_download_and_machine_apply(tmp_path):
    settings = Settings()
    token = settings.prototype_enrollment_token()
    assert token
    key = Ed25519PrivateKey.generate()
    device_uuid = uuid4()
    enrollment = {"X-Flexmix-Prototype-Enrollment-Token": token}

    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    with factory() as session:
        replace_catalogue(
            session,
            ingredients=(
                IngredientDraft("water", "Water", "PUMP"),
                IngredientDraft("milk", "Milk", "PUMP"),
                IngredientDraft("tea", "Tea", "PUMP"),
            ),
            drinks=(
                DrinkDraft("latte", "Latte", 350, True, (RecipeActionDraft("milk", 100),)),
                DrinkDraft("tea", "Tea", 250, True, (RecipeActionDraft("tea", 10),)),
            ),
        )
    engine.dispose()

    with TestClient(create_app(settings)) as client:
        registered = client.post(
            "/v1/prototype/fleet/machines",
            headers=enrollment,
            json={"device_uuid": str(device_uuid), "device_public_key": key_text(key)},
        )
        assert registered.status_code == 201
        headers = {
            "X-Flexmix-Device-Uuid": str(device_uuid),
            "X-Flexmix-Device-Signature": b64encode(
                key.sign(request_payload("GET", "/v1/state", device_uuid))
            ).decode("ascii"),
        }
        snapshot = client.get("/v1/state", headers=headers)
        assert snapshot.status_code == 200
        body = snapshot.json()
        assert body["target_mid"] == registered.json()["mid"]
        assert body["version"] >= 2
        assert [drink["id"] for drink in body["drinks"]] == ["latte", "tea"]

        from flexmix_machine.desired_state import LocalDesiredState
        local = LocalDesiredState(tmp_path / "state.json", mid=body["target_mid"], available_ingredient_ids={"milk"})
        first = local.apply(body)
        second = local.apply(body)
        assert first == second
        assert [drink["id"] for drink in first["drinks"]] == ["latte"]
        assert local.load() == first

        same_version = client.get("/v1/state", params={"have": body["version"]}, headers=headers)
        assert same_version.status_code == 304


def test_local_state_survives_hub_unavailable(tmp_path):
    from flexmix_machine.desired_state import LocalDesiredState
    local = LocalDesiredState(tmp_path / "state.json", mid=7, available_ingredient_ids={"water"})
    snapshot = {
        "contract": "flexmix-desired-state-prototype-v1",
        "version": 1,
        "target_mid": 7,
        "ingredients": [{"id": "water", "name": "Water", "kind": "PUMP"}],
        "drinks": [{"id": "water", "name": "Water", "price_cents": 1, "recipe": [{"step_no": 1, "ingredient_id": "water", "amount_grams": 10}]}],
    }
    applied = local.apply(snapshot)
    assert local.load() == applied
    # No Hub call is involved; the last valid local state remains readable offline.
    assert local.path.exists()
