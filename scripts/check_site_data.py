"""Empty-dashboard gate: the built site artifact must contain rows for every
Evidence source. A build that succeeds with empty tables is a presentation
false-positive — this makes it a hard failure before Pages deploy.

Run after `npm run build`: python scripts/check_site_data.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    sources = sorted(p.stem for p in (REPO / "site/sources/fanuni").glob("*.sql"))
    if not sources:
        print("no source queries found — wrong repo layout?")
        return 1
    data_root = REPO / "site" / "build" / "data" / "fanuni"
    failures: list[str] = []
    for name in sources:
        # Layout: data/fanuni/<name>/<content-hash>/<name>.parquet
        parquets = sorted((data_root / name).glob(f"*/{name}.parquet"))
        if not parquets:
            failures.append(f"{name}: parquet missing from build artifact")
            continue
        for parquet in parquets:
            row = duckdb.sql(f"select count(*) from '{parquet.as_posix()}'").fetchone()
            count = int(row[0]) if row else 0
            if count == 0:
                failures.append(f"{name}: 0 rows in {parquet.parent.name}")
            else:
                print(f"{name}: {count} rows")
    if failures:
        print("EMPTY-DASHBOARD GATE FAILED:\n  " + "\n  ".join(failures))
        return 1
    print(f"all {len(sources)} sources populated in the build artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
