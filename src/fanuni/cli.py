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

    args = parser.parse_args(argv)

    if args.command == "info":
        settings = load_settings()
        print(f"fanuni {__version__}")
        print(f"  database_url    = {settings.database_url}")
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

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
