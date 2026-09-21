import pytest
from pydantic import ValidationError

from flexmix_hub.config import Settings


def test_missing_configuration_fails(settings):
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_password_url_encoding_and_redaction(settings):
    # Deliberately troublesome synthetic password, not an actual credential.
    password = "synthetic:@/%?# secret"
    settings.db_password_file.write_text(password + "\n")
    url = settings.database_url()
    assert url.password == password
    assert password not in str(url)
    assert password not in repr(settings)


def test_empty_password_rejected(settings):
    settings.db_password_file.write_text("\n")
    with pytest.raises(ValueError, match="must not be empty"):
        settings.database_url()


def test_missing_password_file_rejected(settings):
    settings.db_password_file.unlink()
    with pytest.raises(FileNotFoundError):
        settings.database_url()


def test_environment_overrides_dotenv(settings, tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    env_file.write_text("FLEXMIX_DB_PORT=13306\n")
    monkeypatch.setenv("FLEXMIX_DB_PORT", "13307")
    configured = Settings(
        _env_file=env_file, db_name=settings.db_name, db_user=settings.db_user,
        db_password_file=settings.db_password_file,
    )
    assert configured.db_port == 13307


def test_admin_credentials_accept_unprefixed_environment_names(settings, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "chosen-admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$argon2id$v=19$m=65536,t=3,p=4$hash")
    configured = Settings(
        _env_file=None,
        db_name=settings.db_name,
        db_user=settings.db_user,
        db_password_file=settings.db_password_file,
    )
    assert configured.admin_username == "chosen-admin"
    assert configured.admin_password_hash.get_secret_value().startswith("$argon2id$")
    assert "$argon2id$" not in repr(configured)
