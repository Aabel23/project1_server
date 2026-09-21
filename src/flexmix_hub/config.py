"""Development settings. Passwords are read from files, never defaulted."""

from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FLEXMIX_", env_file=".env", env_file_encoding="utf-8",
        extra="ignore", hide_input_in_errors=True,
    )

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=13306, ge=1, le=65535)
    db_name: str = Field(min_length=1)
    db_user: str = Field(min_length=1)
    db_password_file: Path
    # Prototype-only bootstrap. Production identity is pending Q-12/Q-15.
    prototype_enrollment_token_file: Path | None = None
    admin_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_USERNAME", "FLEXMIX_ADMIN_USERNAME"),
    )
    admin_password_hash: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_PASSWORD_HASH", "FLEXMIX_ADMIN_PASSWORD_HASH"),
    )
    prototype_hub_url: str = "http://127.0.0.1:8001"
    prototype_machine_tailnet_tag: str = "tag:flexmix-machine"
    backup_root: Path = Path("/tmp/flexmix-hub-backups")
    release_root: Path = Path("/tmp/flexmix-hub-releases")

    def database_url(self) -> URL:
        # Remove a conventional file line ending, not password whitespace.
        password = SecretStr(self.db_password_file.read_text().rstrip("\r\n"))
        if not password.get_secret_value():
            raise ValueError("Database password file must not be empty")
        return URL.create(
            "mysql+pymysql", username=self.db_user,
            password=password.get_secret_value(), host=self.db_host,
            port=self.db_port, database=self.db_name,
            query={"charset": "utf8mb4"},
        )

    def prototype_enrollment_token(self) -> str | None:
        """Read the local bootstrap token only when prototype enrollment is used."""
        if self.prototype_enrollment_token_file is None:
            return None
        try:
            token = self.prototype_enrollment_token_file.read_text().rstrip("\r\n")
        except OSError:
            return None
        return token or None
