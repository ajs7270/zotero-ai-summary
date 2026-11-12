"""Check the shipped clients' success and partial-import contracts."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class RegistrationTests(unittest.TestCase):
    def load_client(self, skill):
        path = ROOT / "skill" / skill / "scripts" / "zotero_register_note.py"
        spec = importlib.util.spec_from_file_location(f"register_{skill}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_client(self, skill, response):
        client = self.load_client(skill)
        stdout, stderr = io.StringIO(), io.StringIO()
        calls = []

        def request(url, **kwargs):
            calls.append((url, kwargs))
            if url == client.HEALTH_URL:
                return {"ok": True, "version": "0.0.2", "converter": {
                    "name": "markdown-it", "version": "14.1.0",
                }}
            return response

        argv = ["register", "--parent", "ABCD1234", "--title", "Summary (Test)",
                "--markdown", "-", "--tag", "validation"]
        with patch.object(sys, "argv", argv), patch.object(sys, "stdin", io.StringIO("# Summary (Test)\n\n한국어 $x$")), \
                patch.object(client, "_request", request), contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            code = client.main()
        return code, stdout.getvalue(), stderr.getvalue(), calls

    def test_success_sends_markdown_parent_title_and_tags(self):
        for skill in ("summary", "pinpoint-lesson"):
            with self.subTest(skill=skill):
                code, stdout, stderr, calls = self.run_client(skill, {
                    "ok": True, "key": "NOTE1234", "imageFailures": [],
                })
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(stdout)["key"], "NOTE1234")
                self.assertEqual(len(calls), 2)
                payload = json.loads(calls[1][1]["body"])
                self.assertEqual(payload, {
                    "parentItem": "ABCD1234", "title": "Summary (Test)",
                    "markdown": "# Summary (Test)\n\n한국어 $x$", "tags": ["validation"],
                })

    def test_partial_image_import_is_a_failure_with_repairable_saved_key(self):
        for skill in ("summary", "pinpoint-lesson"):
            with self.subTest(skill=skill):
                code, stdout, stderr, calls = self.run_client(skill, {
                    "ok": True, "key": "NOTE1234", "imageFailures": [{"src": "/missing.png"}],
                })
                self.assertEqual(code, 3)
                self.assertEqual(json.loads(stdout)["key"], "NOTE1234")
                self.assertIn("do not blindly POST again", stderr)
                self.assertEqual(len(calls), 2, "Partial imports must not trigger duplicate POSTs")


if __name__ == "__main__":
    unittest.main()
