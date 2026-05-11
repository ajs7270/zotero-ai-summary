#!/usr/bin/env python3
"""POST a markdown summary to the AI Summary for Zotero plugin.

Reads markdown from a file (or stdin), POSTs it to ``/aisummary/note``
with the supplied parent item key, title, and tags, and prints the resulting
JSON response. Exits non-zero on HTTP error.

The plugin must be installed and Zotero must be running. The plugin's
health endpoint is checked first; on any failure the script prints a
diagnostic and exits with status 2.

Usage:
    python3 zotero_register_note.py \\
        --parent ABCD1234 \\
        --title "Paper Summary (Foo)" \\
        --markdown summary.md \\
        --tag a --tag b
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


PLUGIN_BASE = "http://localhost:23119/aisummary"
HEALTH_URL = f"{PLUGIN_BASE}/health"
NOTE_URL = f"{PLUGIN_BASE}/note"
MIN_PLUGIN_VERSION = (0, 0, 1)


def _parse_version(value: object) -> tuple[int, ...]:
    parts = []
    for piece in str(value or "").split("."):
        digits = ""
        for char in piece:
            if not char.isdigit():
                break
            digits += char
        parts.append(int(digits or "0"))
    return tuple(parts)


def _version_label(version: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)


def _request(url: str, method: str = "GET", body: bytes | None = None, timeout: float = 60.0) -> dict:
    request = urllib.request.Request(
        url=url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", "replace")
        hint = ""
        if method == "GET" and exc.code == 404:
            hint = " Zotero is running, but AI Summary for Zotero is not installed or is disabled."
        elif method == "POST" and exc.code == 404:
            hint = " The parent Zotero item key was not found in the user library."
        raise SystemExit(f"HTTP {exc.code} for {method} {url}: {message.strip()}.{hint}")
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise SystemExit(
            f"Cannot reach {url}: {reason}. Start Zotero, then confirm AI Summary for Zotero is installed and enabled."
        )
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Unexpected non-JSON response from {url}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="POST a markdown summary to AI Summary for Zotero.")
    parser.add_argument("--parent", required=True, help="Parent Zotero item key (8-character)")
    parser.add_argument("--title", required=True, help="Note title (used as fallback if H1 is dropped)")
    parser.add_argument("--markdown", required=True, type=Path, help="Path to the markdown file ('-' to read stdin)")
    parser.add_argument("--tag", action="append", default=[], help="Tag to apply (repeatable)")
    parser.add_argument("--timeout", type=float, default=180.0, help="Request timeout in seconds (default 180)")
    args = parser.parse_args()

    if str(args.markdown) == "-":
        markdown_text = sys.stdin.read()
    else:
        try:
            markdown_text = args.markdown.read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Cannot read markdown file {args.markdown}: {exc}") from exc

    health = _request(HEALTH_URL, timeout=10)
    if not health.get("ok"):
        raise SystemExit(f"Plugin health check failed: {health}")
    plugin_version = _parse_version(health.get("version"))
    if plugin_version < MIN_PLUGIN_VERSION:
        raise SystemExit(
            "AI Summary for Zotero plugin is too old: "
            f"v{health.get('version')} is running, but v{_version_label(MIN_PLUGIN_VERSION)} or later is required. "
            "Update the Zotero plugin before registering notes."
        )
    converter = health.get("converter")
    if converter:
        sys.stderr.write(f"Plugin v{health.get('version')} ready (converter: {converter.get('name')} {converter.get('version')}).\n")
    else:
        raise SystemExit("AI Summary for Zotero health response did not report the bundled markdown converter.")

    payload = json.dumps({
        "parentItem": args.parent,
        "title": args.title,
        "markdown": markdown_text,
        "tags": list(args.tag),
    }, ensure_ascii=False).encode("utf-8")

    response = _request(NOTE_URL, method="POST", body=payload, timeout=args.timeout)
    if not response.get("ok") and response.get("error"):
        raise SystemExit(f"AI Summary for Zotero rejected the note: {response.get('error')}")
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
