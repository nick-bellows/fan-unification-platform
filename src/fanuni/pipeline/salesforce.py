"""Salesforce REST extractor client.

Speaks the real protocol shape: OAuth client-credentials token exchange, SOQL
query with a SystemModstamp watermark, and nextRecordsUrl pagination. Locally
it talks to the mock; against a real org only base_url and credentials change.
"""

from __future__ import annotations

from typing import Any

import httpx

API_VERSION = "v59.0"


def build_soql(sobject: str, after: str | None) -> str:
    soql = f"SELECT Fields(ALL) FROM {sobject}"
    if after:
        soql += f" WHERE SystemModstamp > {after}"
    return soql + " ORDER BY SystemModstamp"


class SalesforceClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = httpx.Client(base_url=self._base_url, timeout=30)
        self._token: str | None = None

    def _authenticate(self) -> str:
        response = self._http.post(
            "/services/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        token: str = response.json()["access_token"]
        return token

    def query_all(self, soql: str) -> list[dict[str, Any]]:
        """Run a query and follow nextRecordsUrl until done."""
        if self._token is None:
            self._token = self._authenticate()
        headers = {"Authorization": f"Bearer {self._token}"}

        records: list[dict[str, Any]] = []
        response = self._http.get(
            f"/services/data/{API_VERSION}/query", params={"q": soql}, headers=headers
        )
        response.raise_for_status()
        body = response.json()
        records.extend(body["records"])
        while not body["done"]:
            response = self._http.get(body["nextRecordsUrl"], headers=headers)
            response.raise_for_status()
            body = response.json()
            records.extend(body["records"])
        return records

    def close(self) -> None:
        self._http.close()
