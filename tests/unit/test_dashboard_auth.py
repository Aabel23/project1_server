from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from flexmix_hub.api.dashboard import COOKIE
from flexmix_hub.config import Settings
from flexmix_hub.main import create_app


def test_dashboard_login_uses_admin_credentials_and_rejects_enrollment_token(settings):
    configured = Settings(
        _env_file=None,
        db_name=settings.db_name,
        db_user=settings.db_user,
        db_password_file=settings.db_password_file,
        admin_username="operator",
        admin_password_hash=PasswordHasher().hash("correct horse battery staple"),
        prototype_enrollment_token_file=None,
    )
    with TestClient(create_app(configured)) as client:
        assert client.get("/login").status_code == 200
        assert client.post("/login", data={"token": "correct horse battery staple"}).status_code == 401
        assert client.post("/login", data={"username": "operator", "password": "wrong"}).status_code == 401
        response = client.post(
            "/login", data={"username": "operator", "password": "correct horse battery staple"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.cookies.get(COOKIE)
        assert "httponly" in response.headers["set-cookie"].lower()
