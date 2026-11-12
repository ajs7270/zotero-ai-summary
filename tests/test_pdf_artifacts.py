"""Test artifact manifests across repeated extraction into the same directory."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skill/summary/scripts/prepare_pdf_artifacts.py"
SPEC = importlib.util.spec_from_file_location("prepare_pdf_artifacts", HELPER)
artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifacts)


class PdfArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-summary-pdf-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / "artifacts"
        self.first_pdf = self.root / "first.pdf"
        self.second_pdf = self.root / "second.pdf"
        self.first_pdf.write_bytes(b"first PDF fixture")
        self.second_pdf.write_bytes(b"second PDF fixture")
        self.fail_render = False
        self.commands = []

    def poppler(self, arguments):
        """Emulate output files while preserving the real extraction pipeline."""
        self.commands.append(arguments)
        command = Path(arguments[0]).name
        stdout = ""
        if command == "pdftotext":
            Path(arguments[-1]).write_text(f"Text from {Path(arguments[-2]).name}")
        elif command == "pdfinfo":
            stdout = "Pages: 4\nTitle: Test paper\n"
        elif command == "pdfimages":
            pdf = Path(arguments[-2])
            prefix = Path(arguments[-1])
            count = 3 if pdf == self.first_pdf else 1
            for number in range(count):
                prefix.with_name(f"{prefix.name}-{number:03d}.png").write_bytes(pdf.name.encode())
        elif command == "pdftoppm":
            if self.fail_render:
                raise SystemExit("pdftoppm failed: simulated render failure")
            prefix = Path(arguments[-1])
            first = int(arguments[arguments.index("-f") + 1]) if "-f" in arguments else 1
            last = int(arguments[arguments.index("-l") + 1]) if "-l" in arguments else 4
            for number in range(first, last + 1):
                prefix.with_name(f"{prefix.name}-{number:03d}.png").write_bytes(b"rendered page")
        else:
            self.fail(f"Unexpected Poppler command: {arguments}")
        return subprocess.CompletedProcess(arguments, 0, stdout=stdout, stderr="")

    def extract(self, pdf, *options):
        argv = [str(HELPER), str(pdf), "--out", str(self.output), *options]
        capture = io.StringIO()
        with patch("sys.argv", argv), patch.object(
            artifacts.shutil, "which", side_effect=lambda name: f"/mock/{name}"
        ), patch.object(artifacts, "run_command", side_effect=self.poppler), contextlib.redirect_stdout(capture):
            self.assertEqual(artifacts.main(), 0)
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(json.loads(capture.getvalue())["embedded_images"], manifest["embedded_images"])
        return manifest

    def test_new_pdf_excludes_old_figures_and_pages_without_deleting_manual_crop(self):
        first = self.extract(self.first_pdf, "--render-pages")
        self.assertEqual(first["embedded_image_count"], 3)
        self.assertEqual(first["page_render_count"], 4)
        manual = self.output / "images" / "manual-crop.png"
        manual.write_bytes(b"keep manual crop")

        second = self.extract(self.second_pdf)
        self.assertEqual(second["pdf"], str(self.second_pdf))
        self.assertEqual(second["embedded_image_count"], 1)
        self.assertEqual(second["page_renders"], [])
        self.assertEqual(second["page_render_count"], 0)
        self.assertEqual(
            second["embedded_images"], [str(self.output / "images" / "figure-000.png")],
        )
        self.assertEqual(manual.read_bytes(), b"keep manual crop")
        self.assertTrue((self.output / "images" / "figure-002.png").is_file())
        self.assertEqual((self.output / "fulltext.txt").read_text(), "Text from second.pdf")

    def test_smaller_render_range_excludes_previous_pages(self):
        self.extract(self.first_pdf, "--render-pages", "--render-page-range", "1-4")
        current = self.extract(self.first_pdf, "--render-pages", "--render-page-range", "2-2")
        self.assertEqual(current["page_render_count"], 1)
        self.assertEqual(current["page_renders"], [str(self.output / "pages" / "page-002.png")])
        self.assertTrue((self.output / "pages" / "page-004.png").is_file())
        self.assertTrue(all(Path(path).is_file() for path in current["embedded_images"] + current["page_renders"]))

    def test_failed_extraction_preserves_previous_manifest_and_text(self):
        self.extract(self.first_pdf, "--render-pages")
        manifest = (self.output / "manifest.json").read_bytes()
        text = (self.output / "fulltext.txt").read_bytes()
        self.fail_render = True
        with self.assertRaisesRegex(SystemExit, "simulated render failure"):
            self.extract(self.second_pdf, "--render-pages")
        self.assertEqual((self.output / "manifest.json").read_bytes(), manifest)
        self.assertEqual((self.output / "fulltext.txt").read_bytes(), text)
        self.assertEqual(list(self.output.glob(".extract-*")), [])

    def test_invalid_dpi_fails_before_running_poppler(self):
        for dpi in ("0", "-1"):
            with self.subTest(dpi=dpi):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    self.extract(self.first_pdf, "--page-dpi", dpi)
                self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.commands, [])
        self.assertFalse(self.output.exists())

    def test_invalid_page_ranges_fail_before_creating_output(self):
        for value in ("0-2", "4-2", "1", "a-b", "1-2-3"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.extract(self.first_pdf, "--render-pages", "--render-page-range", value)
                self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.output.exists())

    def test_image_prefix_cannot_escape_staging_directory(self):
        for value in ("../outside", "/absolute", ".", ".."):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.extract(self.first_pdf, "--image-prefix", value)
                self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.output.exists())

    def test_both_skills_ship_the_same_helper(self):
        counterpart = ROOT / "skill/pinpoint-lesson/scripts/prepare_pdf_artifacts.py"
        self.assertEqual(HELPER.read_bytes(), counterpart.read_bytes())


if __name__ == "__main__":
    unittest.main()
