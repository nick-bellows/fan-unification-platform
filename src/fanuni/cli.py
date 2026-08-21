"""Command-line entry point.

Subcommands are added as milestones land; `info` exists from M0 so the
installed console script is verifiable from day one.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from fanuni import __version__
from fanuni.config import load_settings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fanuni", description=__doc__)
    parser.add_argument("--version", action="version", version=f"fanuni {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="show version and resolved (non-secret) configuration")

    gen = sub.add_parser("generate", help="generate the synthetic sources + ground truth")
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--fans", type=int, default=5000)
    gen.add_argument("--out", default="data")

    sub.add_parser("init-db", help="create warehouse schemas and ops/raw tables (idempotent)")

    ing = sub.add_parser("ingest", help="run the extraction/load flows")
    ing.add_argument("--source", choices=["all", "crm", "files"], default="all")
    ing.add_argument("--full-refresh", action="store_true", help="ignore the CRM watermark")
    ing.add_argument("--force", action="store_true", help="reload files even if unchanged")
    ing.add_argument("--start-month", help="backfill lower bound, YYYY-MM")
    ing.add_argument("--end-month", help="backfill upper bound, YYYY-MM")

    tra = sub.add_parser("transform", help="staging models -> unification -> core/marts models")
    tra.add_argument(
        "--select",
        nargs="+",
        help="rerun just these models directly (skips unification and audit ordering)",
    )

    sub.add_parser("dq", help="run the data-quality gates (error severity fails)")

    uni = sub.add_parser("unify", help="rebuild identity.fan_xref + identity.golden_fans")
    uni.add_argument("--mode", choices=["deterministic", "full"], default="full")

    ev = sub.add_parser(
        "evaluate", help="score unification against ground truth (baseline vs full)"
    )
    ev.add_argument("--truth", default="data/truth/record_map.csv")
    ev.add_argument("--out", default="eval/results")
    ev.add_argument("--review-dir", default="data/review")
    ev.add_argument(
        "--sweep",
        action="store_true",
        help="run the auto-merge threshold sweep instead of the standard eval",
    )

    pipe = sub.add_parser("pipeline", help="full nightly run: ingest -> transform -> dq")
    pipe.add_argument("--full-refresh", action="store_true")
    pipe.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "info":
        import re

        settings = load_settings()
        masked_dsn = re.sub(r"(://[^:/@]+):[^@]+@", r"\1:***@", settings.database_url)
        print(f"fanuni {__version__}")
        print(f"  database_url    = {masked_dsn}")
        print(f"  s3_endpoint_url = {settings.s3_endpoint_url}")
        print(f"  lake_bucket     = {settings.lake_bucket}")
        print(f"  sf_base_url     = {settings.sf_base_url}")
        return 0

    if args.command == "generate":
        from fanuni.generator.model import GenConfig
        from fanuni.generator.run import generate

        manifest = generate(GenConfig(seed=args.seed, fans=args.fans, out_dir=args.out))
        print(json.dumps(manifest["counts"], indent=2))
        print(f"wrote synthetic sources + ground truth under {args.out}/")
        return 0

    if args.command == "init-db":
        from pathlib import Path

        from fanuni.pipeline.db import connect, run_sql_dir

        settings = load_settings()
        with connect(settings) as conn:
            executed = run_sql_dir(conn, Path(settings.warehouse_dir) / "ddl")
        print(f"executed: {', '.join(executed)}")
        return 0

    if args.command == "ingest":
        from fanuni.pipeline.flows import ingest_file_sources, ingest_salesforce

        counts: dict[str, int] = {}
        if args.source in ("all", "crm"):
            counts.update(ingest_salesforce(full_refresh=args.full_refresh))
        if args.source in ("all", "files"):
            counts.update(
                ingest_file_sources(
                    start_month=args.start_month,
                    end_month=args.end_month,
                    force=args.force,
                )
            )
        print(json.dumps(counts, indent=2))
        return 0

    if args.command == "transform":
        if args.select:
            from pathlib import Path

            from fanuni.pipeline.db import connect, finish_run, start_run
            from fanuni.pipeline.sql_runner import run_models

            settings = load_settings()
            with connect(settings) as conn:
                run_id = start_run(conn, "transform-select", {"select": args.select})
                try:
                    results = run_models(
                        conn, Path(settings.warehouse_dir) / "models", run_id, select=args.select
                    )
                except Exception:
                    finish_run(conn, run_id, "failed")
                    raise
                finish_run(conn, run_id, "completed")
            for result in results:
                print(f"{result.model.schema}.{result.model.table}: {result.rows} rows")
            return 0
        from fanuni.pipeline.flows import transform_warehouse

        print(json.dumps(transform_warehouse(), indent=2))
        return 0

    if args.command == "dq":
        from fanuni.pipeline.flows import run_quality_gates

        print(json.dumps(run_quality_gates(), indent=2))
        return 0

    if args.command == "unify":
        from fanuni.pipeline.db import connect
        from fanuni.unification.run import run_unification

        settings = load_settings()
        with connect(settings) as conn:
            stats = run_unification(conn, mode=args.mode)
        print(json.dumps(stats, indent=2))
        return 0

    if args.command == "evaluate":
        from pathlib import Path

        from fanuni.pipeline.db import connect
        from fanuni.unification.evaluate import run_eval, run_threshold_sweep

        settings = load_settings()
        if args.sweep:
            with connect(settings) as conn:
                rows = run_threshold_sweep(conn, Path(args.truth), Path(args.out))
            for row in rows:
                threshold = row["threshold"] if row["threshold"] is not None else "baseline"
                print(
                    f"{row['variant']} @ {threshold}: precision={row['precision']:.4f}"
                    f" recall={row['recall']:.4f} f1={row['f1']:.4f}"
                )
            print(f"sweep written to {args.out}/threshold_sweep.md")
            return 0
        with connect(settings) as conn:
            report = run_eval(conn, Path(args.truth), Path(args.out), Path(args.review_dir))
        for variant, data in report["variants"].items():
            m = data["metrics"]
            print(
                f"{variant}: precision={m['precision']:.4f}"
                f" recall={m['recall']:.4f} f1={m['f1']:.4f}"
            )
        print(f"review band: {report['review_band']} pairs")
        print(f"reports written to {args.out}/")
        return 0

    if args.command == "pipeline":
        from fanuni.pipeline.flows import nightly_pipeline

        outcome = nightly_pipeline(full_refresh=args.full_refresh, force=args.force)
        print(json.dumps(outcome, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
