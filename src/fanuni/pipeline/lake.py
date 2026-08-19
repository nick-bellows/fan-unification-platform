"""Object-store ("lake") access.

Genuine boto3 against an S3 API; locally that's MinIO via endpoint_url, and
pointing the identical code at AWS S3 means dropping the endpoint override
(see ADR 0002).
"""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from fanuni.config import Settings


def s3_client(settings: Settings) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 5}),
    )


def ensure_bucket(client: Any, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)


def put_bytes(client: Any, bucket: str, key: str, body: bytes) -> None:
    client.put_object(Bucket=bucket, Key=key, Body=body)


def put_jsonl(client: Any, bucket: str, key: str, rows: list[dict[str, Any]]) -> int:
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    put_bytes(client, bucket, key, body)
    return len(body)


def get_bytes(client: Any, bucket: str, key: str) -> bytes:
    body: bytes = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    return body


def list_keys(client: Any, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    return keys
