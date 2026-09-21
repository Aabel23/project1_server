import secrets

import pytest

from flexmix_hub.config import Settings


@pytest.fixture
def settings(tmp_path, monkeypatch):
    # Unit tests never consume developer .env or database credentials.
    import os

    for name in tuple(os.environ):
        if name.startswith("FLEXMIX_"):
            monkeypatch.delenv(name)
    password_file = tmp_path / "password"
    password_file.write_text(secrets.token_urlsafe(24))
    return Settings(
        _env_file=None, db_name="unit_test", db_user="unit_test",
        db_password_file=password_file,
    )
