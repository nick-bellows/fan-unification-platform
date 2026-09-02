"""Serve the static Evidence build under its configured GitHub Pages base path."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "site" / "build"
BASE_PATH = "/fan-unification-platform"


class BasePathHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        request_path = unquote(urlsplit(path).path)
        if request_path == BASE_PATH:
            request_path = "/"
        elif request_path.startswith(f"{BASE_PATH}/"):
            request_path = request_path[len(BASE_PATH) :]
        else:
            request_path = "/__missing__"
        relative = request_path.lstrip("/")
        candidate = (BUILD / relative).resolve()
        if BUILD.resolve() not in (candidate, *candidate.parents):
            return str(BUILD / "__missing__")
        return str(candidate)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    if not (BUILD / "index.html").exists():
        raise SystemExit("site/build is missing; run npm run build:strict first")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), BasePathHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
