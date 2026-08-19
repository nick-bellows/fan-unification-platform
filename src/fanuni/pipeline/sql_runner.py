"""The transform runner: ordered SQL models, executed with an audit trail.

Layout: warehouse/models/<layer>/<NN>_<table>.sql. The layer directory maps to
the schema; the numeric prefix fixes execution order inside a layer; the rest
of the stem is the table the model builds. Each model is a plain SQL script —
full-rebuild models DROP+CREATE their table, incremental models CREATE IF NOT
EXISTS + insert what's new. Row counts and durations land in ops.model_runs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg

LAYER_SCHEMAS: dict[str, str] = {
    "10_staging": "staging",
    "30_core": "core",
    "40_marts": "marts",
}


@dataclass(frozen=True)
class Model:
    path: Path
    layer: str
    schema: str
    table: str


@dataclass(frozen=True)
class ModelResult:
    model: Model
    rows: int
    duration_ms: int


def discover_models(models_dir: Path, layers: list[str] | None = None) -> list[Model]:
    models: list[Model] = []
    for layer_dir in sorted(p for p in models_dir.iterdir() if p.is_dir()):
        schema = LAYER_SCHEMAS.get(layer_dir.name)
        if schema is None:
            continue
        if layers and schema not in layers:
            continue
        for sql_file in sorted(layer_dir.glob("*.sql")):
            prefix, _, table = sql_file.stem.partition("_")
            if not prefix.isdigit() or not table:
                raise ValueError(f"model file not named NN_table.sql: {sql_file}")
            models.append(Model(sql_file, layer_dir.name, schema, table))
    return models


def run_models(
    conn: psycopg.Connection[Any],
    models_dir: Path,
    run_id: str,
    layers: list[str] | None = None,
    select: list[str] | None = None,
) -> list[ModelResult]:
    results: list[ModelResult] = []
    for model in discover_models(models_dir, layers):
        if select and model.table not in select:
            continue
        started = time.perf_counter()
        conn.execute(model.path.read_text(encoding="utf-8"))
        duration_ms = int((time.perf_counter() - started) * 1000)
        row = conn.execute(f"SELECT count(*) FROM {model.schema}.{model.table}").fetchone()
        rows = int(row[0]) if row else 0
        conn.execute(
            """
            INSERT INTO ops.model_runs (run_id, model, schema_name, rows, duration_ms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, model.table, model.schema, rows, duration_ms),
        )
        conn.commit()
        results.append(ModelResult(model, rows, duration_ms))
    return results
