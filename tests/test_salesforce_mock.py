from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import fanuni.salesforce_mock.app as sfmock
from fanuni.salesforce_mock.app import app


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.fixture()
def client(small_dataset: tuple[Path, dict], monkeypatch: pytest.MonkeyPatch) -> TestClient:
    out, _ = small_dataset
    monkeypatch.setenv("FANUNI_SF_DATA_DIR", str(out / "sfmock"))
    return TestClient(app)


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "fanuni-dev-client",
            "client_secret": "dev-client-secret",
        },
    )
    assert response.status_code == 200
    token: str = response.json()["access_token"]
    return token


def test_token_rejects_bad_client(client: TestClient) -> None:
    response = client.post(
        "/services/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": "x", "client_secret": "y"},
    )
    assert response.status_code == 401


def test_query_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/services/data/v59.0/query", params={"q": "SELECT Id FROM Contact"})
    assert response.status_code == 401


def test_query_paginates_like_an_extractor_would(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sfmock, "PAGE_SIZE", 25)
    headers = {"Authorization": f"Bearer {_get_token(client)}"}

    body = client.get(
        "/services/data/v59.0/query",
        params={"q": "SELECT Id FROM Contact ORDER BY SystemModstamp"},
        headers=headers,
    ).json()
    total = body["totalSize"]
    assert total > 25
    seen = [r["Id"] for r in body["records"]]
    while not body["done"]:
        body = client.get(body["nextRecordsUrl"], headers=headers).json()
        seen.extend(r["Id"] for r in body["records"])
    assert len(seen) == total == len(set(seen))

    # Modstamps arrive in ascending order — what watermarking relies on.
    stamps_body = client.get(
        "/services/data/v59.0/query",
        params={"q": "SELECT Id FROM Contact ORDER BY SystemModstamp LIMIT 2000"},
        headers=headers,
    )
    assert stamps_body.status_code == 200


def test_watermark_filter(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {_get_token(client)}"}
    everything = client.get(
        "/services/data/v59.0/query",
        params={"q": "SELECT Id FROM Contact"},
        headers=headers,
    ).json()
    watermark = "2026-01-01T00:00:00Z"
    filtered = client.get(
        "/services/data/v59.0/query",
        params={"q": f"SELECT Id FROM Contact WHERE SystemModstamp > {watermark}"},
        headers=headers,
    ).json()
    assert 0 < filtered["totalSize"] < everything["totalSize"]
    assert all(r["SystemModstamp"] > watermark for r in filtered["records"])


def test_opportunities_served(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {_get_token(client)}"}
    body = client.get(
        "/services/data/v59.0/query",
        params={"q": "SELECT Id FROM Opportunity"},
        headers=headers,
    ).json()
    assert body["totalSize"] > 0
    assert body["records"][0]["attributes"]["type"] == "Opportunity"
