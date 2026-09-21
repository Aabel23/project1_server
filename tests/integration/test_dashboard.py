import os
from html import unescape
import pytest
from fastapi.testclient import TestClient
from flexmix_hub.config import Settings
from flexmix_hub.main import create_app
from flexmix_hub.api.dashboard import NAV_GROUPS

pytestmark = pytest.mark.skipif(os.environ.get("FLEXMIX_TEST_MYSQL") != "1", reason="MySQL required")

def test_dashboard_renders_fleet_and_catalogue():
    settings = Settings(); token = settings.prototype_enrollment_token(); assert token
    with TestClient(create_app(settings)) as client:
        assert client.get("/", follow_redirects=False).status_code == 303
        assert client.get("/login").status_code == 200
        assert client.get(f"/?token={token}", follow_redirects=False).status_code == 303
        login = client.post("/login", data={"token": token}, follow_redirects=False)
        assert login.status_code == 303
        assert "httponly" in login.headers["set-cookie"].lower()
        response = client.get("/")
        assert response.status_code == 200
        assert "FlexMix Hub" in response.text and "Catalogue version" in response.text and "MID" in response.text
        assert "Recent Events" in response.text and "Recent Commands" in response.text
        for group, items in NAV_GROUPS:
            assert group in response.text
            for label, slug in items:
                assert f'href="/admin/{slug}"' in response.text
                page = client.get(f"/admin/{slug}")
                assert page.status_code == 200, slug
                assert label in unescape(page.text)
        assert client.get("/static/dashboard.css").status_code == 200
        assert client.post("/logout", follow_redirects=False).status_code == 303
        assert client.get("/", follow_redirects=False).status_code == 303
        assert client.get("/admin/machine-fleet", follow_redirects=False).status_code == 303
