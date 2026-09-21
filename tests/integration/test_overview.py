import os
from fastapi.testclient import TestClient
import pytest
from flexmix_hub.config import Settings
from flexmix_hub.main import create_app

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")

def test_overview_requires_token_and_is_read_only():
    settings = Settings(); token = settings.prototype_enrollment_token(); assert token
    with TestClient(create_app(settings)) as client:
        assert client.get("/v1/prototype/overview").status_code == 401
        headers = {"X-Flexmix-Prototype-Enrollment-Token": token}
        first = client.get("/v1/prototype/overview", headers=headers)
        second = client.get("/v1/prototype/overview", headers=headers)
        assert first.status_code == second.status_code == 200
        assert [m["mid"] for m in first.json()["machines"]] == [m["mid"] for m in second.json()["machines"]]
        assert [m["event_count"] for m in first.json()["machines"]] == [m["event_count"] for m in second.json()["machines"]]
