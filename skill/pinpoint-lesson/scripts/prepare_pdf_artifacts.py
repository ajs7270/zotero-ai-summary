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
import tempfile
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
    image_paths: list[Path],
    page_paths: list[Path],
) -> dict[str, object]:
    image_dir = output_dir / "images"
    page_dir = output_dir / "pages"
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
    if args.page_dpi <= 0:
        parser.error("--page-dpi must be a positive integer")
    page_range: tuple[int, int] | None = None
    if args.render_page_range:
        try:
            first, last = (int(value) for value in args.render_page_range.split("-", 1))
        except ValueError:
            parser.error("--render-page-range must use positive 'first-last' values, for example '1-12'")
        if first < 1 or last < first:
            parser.error("--render-page-range must start at 1 or later and end at or after the first page")
        page_range = (first, last)
    if not args.image_prefix or Path(args.image_prefix).name != args.image_prefix or args.image_prefix in {".", ".."}:
        parser.error("--image-prefix must be a filename prefix without directory components")

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

    manifest_path = output_dir / "manifest.json"
    text_path = output_dir / "fulltext.txt"
    # Extract in a fresh directory so reusing --out cannot add a previous PDF's
    # figures, manual crops, or pages outside the current range to the manifest.
    # Publish only this run's files; leave unrelated user-created files intact.
    with tempfile.TemporaryDirectory(prefix=".extract-", dir=output_dir) as temporary:
        staging = Path(temporary)
        staged_images = staging / "images"
        staged_pages = staging / "pages"
        staged_images.mkdir()
        staged_pages.mkdir()
        staged_text = staging / "fulltext.txt"
        run_command([pdftotext_path, "-layout", "-enc", "UTF-8", str(pdf_path), str(staged_text)])

        metadata: dict[str, str] = {}
        if pdfinfo_path:
            metadata = parse_pdfinfo(run_command([pdfinfo_path, str(pdf_path)]).stdout)

        run_command([pdfimages_path, "-png", str(pdf_path), str(staged_images / args.image_prefix)])
        if args.render_pages:
            cmd = [pdftoppm_path, "-png", "-r", str(args.page_dpi)]
            if page_range:
                cmd += ["-f", str(page_range[0]), "-l", str(page_range[1])]
            cmd += [str(pdf_path), str(staged_pages / "page")]
            run_command(cmd)

        image_paths = [image_dir / path.name for path in sorted(staged_images.glob("*.png"))]
        page_paths = [page_dir / path.name for path in sorted(staged_pages.glob("*.png"))]
        manifest = build_manifest(
            pdf_path, output_dir, text_path, metadata, args.page_dpi, image_paths, page_paths,
        )
        staged_manifest = staging / "manifest.json"
        staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        for directory, destination in ((staged_images, image_dir), (staged_pages, page_dir)):
            for path in directory.iterdir():
                path.replace(destination / path.name)
        staged_text.replace(text_path)
        staged_manifest.replace(manifest_path)

    print(json.dumps({"manifest": str(manifest_path), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
