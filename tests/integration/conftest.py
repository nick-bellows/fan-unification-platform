"""Shared fixtures for the integration suite.

The modules in this directory are ordered stages of one pipeline story
(test_ingest runs before test_transform — pytest collects alphabetically) and
share one generated dataset and one warehouse reset per session.
"""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

from fanuni.config import load_settings
from fanuni.generator.model import GenConfig
from fanuni.generator.run import generate

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED = 1234
FANS = 800


def _endpoint(url: str, default_port: int) -> tuple[str, int]:
    parsed = urlparse(url if "://" in url else f"scheme://{url}")
    return parsed.hostname or "localhost", parsed.port or default_port


@pytest.fixture(scope="session")
def stack() -> Any:
    os.environ["FANUNI_DROPZONE_DIR"] = str(REPO_ROOT / "data" / "dropzone")
    os.environ["FANUNI_WAREHOUSE_DIR"] = str(REPO_ROOT / "warehouse")
    os.environ.setdefault("PREFECT_API_URL", "http://localhost:4200/api")
    settings = load_settings()

    needed = [
        _endpoint(settings.database_url, 5432),
        _endpoint(settings.s3_endpoint_url, 9000),
        _endpoint(settings.sf_base_url, 8001),
        _endpoint(os.environ["PREFECT_API_URL"], 4200),
    ]
    down = []
    for host, port in needed:
        try:
            with socket.create_connection((host, port), timeout=2):
                pass
        except OSError:
            down.append(f"{host}:{port}")
    if down:
        message = f"compose stack not reachable: {', '.join(down)}"
        if os.environ.get("FANUNI_REQUIRE_STACK") == "1":
            pytest.fail(message)
        pytest.skip(message)
    return settings


@pytest.fixture(scope="session")
def manifest(stack: Any) -> dict[str, Any]:
    result: dict[str, Any] = generate(
        GenConfig(seed=SEED, fans=FANS, out_dir=str(REPO_ROOT / "data"))
    )
    return result


@pytest.fixture(scope="session")
def fresh_db(stack: Any, manifest: dict[str, Any]) -> Any:
    from fanuni.pipeline.db import connect, run_sql_dir

    conn = connect(stack)
    # Autocommit, or this connection's reads leave an idle-in-transaction
    # session whose AccessShare locks deadlock the pipeline's DROP TABLEs.
    conn.autocommit = True
    for schema in ("raw", "staging", "identity", "core", "marts", "ops"):
        conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    conn.commit()
    run_sql_dir(conn, REPO_ROOT / "warehouse" / "ddl")
    yield conn
    conn.close()
