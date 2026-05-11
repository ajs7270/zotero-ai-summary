#!/usr/bin/env python3
"""Prepare text, metadata, and image artifacts from a PDF for paper summarization.

Two image sources are produced:
  1. ``images/figure-NNN.png`` — original raster images embedded in the PDF
     (via ``pdfimages -png``). These are 1:1 with the source bytes; no
     re-rasterization. Most papers with TikZ/PGF or PDF-vector figures will
     produce only chart accents and screenshot-style figures here, because
     vector graphics are not raster-embedded.
  2. ``pages/page-NNN.png`` — full-page renders at the requested DPI
     (via ``pdftoppm -png``). These are renders, but they faithfully reproduce
     vector figures (architecture diagrams, attention diagrams, plots).
     Use a page render when the relevant figure is missing from
     ``images/`` because it is vector-only.

The note author should prefer ``images/`` whenever the embedded raster
matches a target figure, and fall back to a cropped or full-page ``pages/``
render only when the original figure is vector and unavailable as a raster.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def require_command(name: str) -> str:
    command_path = shutil.which(name)
    if not command_path:
        raise SystemExit(
            f"Missing required command: {name}. Install Poppler tools "
            "(macOS: `brew install poppler`; Ubuntu/Debian: `apt install poppler-utils`)."
        )
    return command_path


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(arguments, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        command = Path(arguments[0]).name
        detail = (exc.stderr or exc.stdout or "").strip()
        if detail:
            raise SystemExit(f"{command} failed: {detail}") from exc
        raise SystemExit(f"{command} failed with exit code {exc.returncode}.") from exc


def parse_pdfinfo(raw_output: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in raw_output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def build_manifest(
    pdf_path: Path,
    output_dir: Path,
    text_path: Path,
    metadata: dict[str, str],
    page_render_dpi: int,
) -> dict[str, object]:
    image_dir = output_dir / "images"
    page_dir = output_dir / "pages"
    image_paths = sorted(image_dir.glob("*.png"))
    page_paths = sorted(page_dir.glob("*.png"))
    return {
        "pdf": str(pdf_path),
        "text": str(text_path),
        "metadata": metadata,
        "embedded_image_dir": str(image_dir),
        "embedded_images": [str(image_path) for image_path in image_paths],
        "embedded_image_count": len(image_paths),
        "page_render_dir": str(page_dir),
        "page_renders": [str(page_path) for page_path in page_paths],
        "page_render_count": len(page_paths),
        "page_render_dpi": page_render_dpi,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PDF text, metadata, embedded images, and page renders with Poppler.")
    parser.add_argument("pdf", type=Path, help="Path to the input PDF")
    parser.add_argument("--out", type=Path, default=None, help="Output directory for extracted artifacts")
    parser.add_argument("--image-prefix", default="figure", help="Prefix for extracted embedded image filenames")
    parser.add_argument("--render-pages", action="store_true", help="Also render every page as a PNG (for vector figures)")
    parser.add_argument("--page-dpi", type=int, default=150, help="DPI for full-page renders (default 150)")
    parser.add_argument("--render-page-range", default=None, help="Optional 'first-last' range to limit page render (e.g. '1-12')")
    args = parser.parse_args()

    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pdftotext_path = require_command("pdftotext")
    pdfimages_path = require_command("pdfimages")
    pdfinfo_path = shutil.which("pdfinfo")
    pdftoppm_path = require_command("pdftoppm") if args.render_pages else shutil.which("pdftoppm")

    output_dir = (args.out or Path.cwd() / f"{pdf_path.stem}-artifacts").expanduser().resolve()
    image_dir = output_dir / "images"
    page_dir = output_dir / "pages"
    image_dir.mkdir(parents=True, exist_ok=True)
    page_dir.mkdir(parents=True, exist_ok=True)

    text_path = output_dir / "fulltext.txt"
    run_command([pdftotext_path, "-layout", "-enc", "UTF-8", str(pdf_path), str(text_path)])

    metadata: dict[str, str] = {}
    if pdfinfo_path:
        metadata = parse_pdfinfo(run_command([pdfinfo_path, str(pdf_path)]).stdout)

    image_prefix_path = image_dir / args.image_prefix
    run_command([pdfimages_path, "-png", str(pdf_path), str(image_prefix_path)])

    if args.render_pages:
        page_prefix = page_dir / "page"
        cmd = [pdftoppm_path, "-png", "-r", str(args.page_dpi)]
        if args.render_page_range:
            try:
                first, last = args.render_page_range.split("-", 1)
            except ValueError as exc:
                raise SystemExit("--render-page-range must use 'first-last', for example '1-12'.") from exc
            cmd += ["-f", first, "-l", last]
        cmd += [str(pdf_path), str(page_prefix)]
        run_command(cmd)

    manifest = build_manifest(pdf_path, output_dir, text_path, metadata, args.page_dpi)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"manifest": str(manifest_path), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
