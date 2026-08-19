"""Runtime configuration.

Every value has a local-development default matching compose.yml, so a clean
clone works with no .env at all. Real deployments override via environment
variables (FANUNI_*); secrets never live in code.
"""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FANUNI_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://fanuni:fanuni_local@localhost:5433/fanuni"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    lake_bucket: str = "fanuni-lake"

    sf_base_url: str = "http://localhost:8001"
    sf_token: SecretStr = SecretStr("dev-local-token")


def load_settings() -> Settings:
    """Build settings from the environment (and .env if present)."""
    return Settings()
