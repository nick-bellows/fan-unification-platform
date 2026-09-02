"""Apply and verify small accessibility/static-hosting fixes to an Evidence build."""

from __future__ import annotations

import argparse
from pathlib import Path

RUNTIME_FIX = """<script data-site-hardening>
(() => {
  const makeTablesKeyboardReachable = () => {
    document.querySelectorAll('.scrollbox').forEach((element) => {
      if (!element.hasAttribute('tabindex')) element.setAttribute('tabindex', '0');
    });
  };
  makeTablesKeyboardReachable();
  new MutationObserver(makeTablesKeyboardReachable).observe(
    document.body, { childList: true, subtree: true }
  );
})();
</script>"""


def harden(html: str) -> str:
    lines = [
        line
        for line in html.splitlines()
        if "favicon.ico" not in line and "apple-touch-icon.png" not in line
    ]
    result = "\n".join(lines) + "\n"
    result = result.replace('<div class="scrollbox ', '<div tabindex="0" class="scrollbox ')
    if "data-site-hardening" not in result:
        result = result.replace("</body>", f"{RUNTIME_FIX}\n</body>")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build = Path(__file__).resolve().parents[1] / "site" / "build"
    pages = sorted(build.rglob("*.html"))
    if not pages:
        raise SystemExit("no built HTML pages found")

    changed = 0
    for page in pages:
        current = page.read_text(encoding="utf-8")
        expected = harden(current)
        if current != expected:
            changed += 1
            if not args.check:
                page.write_text(expected, encoding="utf-8", newline="\n")

    if args.check and changed:
        raise SystemExit(f"{changed} built pages are missing site hardening")
    if not args.check:
        for page in pages:
            rendered = page.read_text(encoding="utf-8")
            if "favicon.ico" in rendered or "apple-touch-icon.png" in rendered:
                raise SystemExit(f"unsupported icon reference remains in {page}")
            if '<div class="scrollbox ' in rendered:
                raise SystemExit(f"non-keyboard-focusable data table remains in {page}")
            if "data-site-hardening" not in rendered:
                raise SystemExit(f"runtime table hardening is missing from {page}")
    print(f"site hardening verified across {len(pages)} HTML pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
