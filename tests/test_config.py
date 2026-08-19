import os

import pytest
from pydantic import SecretStr

from fanuni.config import Settings


def make_settings() -> Settings:
    """Settings isolated from any local .env file (kwarg untyped upstream)."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_defaults_require_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [k for k in os.environ if k.startswith("FANUNI_")]:
        monkeypatch.delenv(key)
    settings = make_settings()
    assert settings.database_url.endswith("/fanuni")
    assert settings.lake_bucket == "fanuni-lake"
    assert isinstance(settings.s3_secret_key, SecretStr)


def test_env_overrides_win(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FANUNI_LAKE_BUCKET", "other-bucket")
    monkeypatch.setenv("FANUNI_SF_TOKEN", "override-token")
    settings = make_settings()
    assert settings.lake_bucket == "other-bucket"
    assert settings.sf_token.get_secret_value() == "override-token"


def test_secrets_do_not_leak_in_repr() -> None:
    settings = make_settings()
    assert "minioadmin" not in repr(settings.s3_secret_key)
    assert "dev-local-token" not in repr(settings.sf_token)
