"""Exercise the installer without touching the user's installed skills or GUI."""

from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-summary-installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "checkout"
        for skill in ("summary", "pinpoint-lesson"):
            directory = self.source / "skill" / skill
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text(f"name: {skill}\n", encoding="utf-8")
        self.targets = self.root / "installed"
        self.plugin_dir = self.root / "plugin-download"
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        # Prevent GUI handoff even on macOS. Other commands remain real.
        self.executable("uname", "#!/bin/sh\nprintf 'Linux\\n'\n")
        self.env = dict(os.environ)
        self.env.update({
            "AI_SUMMARY_LOCAL": str(self.source),
            "AI_SUMMARY_CLIS": "codex",
            "AI_SUMMARY_SKILLS": "summary,pinpoint-lesson",
            "AI_SUMMARY_SKILLS_ROOT": str(self.targets),
            "AI_SUMMARY_PLUGIN_DIR": str(self.plugin_dir),
            "AI_SUMMARY_SKIP_PLUGIN": "1",
            "AI_SUMMARY_SKIP_DEPS_CHECK": "1",
            "PATH": f"{self.bin_dir}{os.pathsep}{self.env['PATH']}",
        })

    def executable(self, name: str, contents: str):
        path = self.bin_dir / name
        path.write_text(contents, encoding="utf-8")
        path.chmod(0o755)

    def run_installer(self, overrides=None, input_text=""):
        environment = dict(self.env)
        environment.update(overrides or {})
        return subprocess.run(
            ["bash", str(INSTALLER)], env=environment,
            input=input_text, text=True, capture_output=True, timeout=15,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_installs_both_skills_for_all_four_targets(self):
        result = self.run_installer({"AI_SUMMARY_CLIS": "claude codex gemini antigravity"})
        self.assert_success(result)
        for cli in ("claude", "codex", "gemini", "antigravity"):
            for skill in ("summary", "pinpoint-lesson"):
                self.assertEqual(
                    (self.targets / cli / skill / "SKILL.md").read_text(),
                    f"name: {skill}\n",
                )

    def test_interactive_antigravity_choice(self):
        result = self.run_installer({"AI_SUMMARY_CLIS": ""}, input_text="4\n")
        self.assert_success(result)
        self.assertTrue((self.targets / "antigravity" / "summary" / "SKILL.md").is_file())
        self.assertFalse((self.targets / "gemini").exists())

    def test_rejects_path_traversal_before_replacing_valid_skill(self):
        existing = self.targets / "codex" / "summary"
        existing.mkdir(parents=True)
        marker = existing / "keep.txt"
        marker.write_text("original")
        result = self.run_installer({"AI_SUMMARY_SKILLS": "summary,../outside"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown skill", result.stderr)
        self.assertEqual(marker.read_text(), "original")

    def test_rejects_unknown_cli_before_replacing_valid_target(self):
        result = self.run_installer({"AI_SUMMARY_CLIS": "codex unknown"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown CLI", result.stderr)
        self.assertFalse(self.targets.exists())

    def test_same_source_and_destination_is_not_deleted(self):
        target = self.targets / "codex" / "summary"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.source / "skill" / "summary", target_is_directory=True)
        result = self.run_installer({"AI_SUMMARY_SKILLS": "summary"})
        self.assert_success(result)
        self.assertIn("already at its source path", result.stderr)
        self.assertTrue(target.is_symlink())
        self.assertEqual((target / "SKILL.md").read_text(), "name: summary\n")

    def test_rejects_destination_containing_source(self):
        # Make the entire checkout a destination, with a source nested below it.
        target = self.targets / "codex" / "summary"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.source, target_is_directory=True)
        result = self.run_installer({"AI_SUMMARY_SKILLS": "summary"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("containing its source", result.stderr)
        self.assertTrue((self.source / "skill" / "summary" / "SKILL.md").is_file())

    def test_copies_local_plugin_to_persistent_handoff_path(self):
        dist = self.source / "dist"
        dist.mkdir()
        (dist / "zotero-ai-summary-0.0.1.xpi").write_bytes(b"test plugin")
        result = self.run_installer({"AI_SUMMARY_SKIP_PLUGIN": "0"}, input_text="y\n")
        self.assert_success(result)
        xpi = self.plugin_dir / "zotero-ai-summary.xpi"
        self.assertEqual(xpi.read_bytes(), b"test plugin")
        self.assertIn(str(xpi), result.stderr)

    def prepare_archive_download(self):
        archive = self.root / "source.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            for skill in ("summary", "pinpoint-lesson"):
                payload = f"name: {skill}\n".encode()
                entry = tarfile.TarInfo(f"repo/skill/{skill}/SKILL.md")
                entry.size = len(payload)
                output.addfile(entry, io.BytesIO(payload))
            payload = b"archived plugin"
            entry = tarfile.TarInfo("repo/dist/zotero-ai-summary-0.0.1.xpi")
            entry.size = len(payload)
            output.addfile(entry, io.BytesIO(payload))
        log = self.root / "curl-urls.txt"
        self.executable("curl", """#!/usr/bin/env python3
import os
from pathlib import Path
import sys
url = next(argument for argument in sys.argv[1:] if argument.startswith('https://'))
with Path(os.environ['TEST_CURL_LOG']).open('a') as output:
    output.write(url + '\\n')
sys.stdout.buffer.write(Path(os.environ['TEST_SOURCE_ARCHIVE']).read_bytes())
""")
        return {"TEST_SOURCE_ARCHIVE": str(archive), "TEST_CURL_LOG": str(log)}, log

    def test_tag_reference_download_and_plugin_survive_source_cleanup(self):
        overrides, log = self.prepare_archive_download()
        overrides.update({
            "AI_SUMMARY_LOCAL": "", "AI_SUMMARY_REF": "v0.0.1",
            "AI_SUMMARY_SKIP_PLUGIN": "0",
        })
        result = self.run_installer(overrides, input_text="y\n")
        self.assert_success(result)
        self.assertIn("/archive/v0.0.1.tar.gz", log.read_text())
        self.assertNotIn("refs/heads/", log.read_text())
        self.assertEqual(
            (self.plugin_dir / "zotero-ai-summary.xpi").read_bytes(), b"archived plugin",
        )
        line = next(line for line in result.stderr.splitlines() if "Downloaded into " in line)
        source_dir = Path(line.split("Downloaded into ", 1)[1])
        self.assertFalse(source_dir.exists(), "Archive extraction directory should be cleaned up")

    def test_branch_with_slash_uses_generic_archive_reference(self):
        overrides, log = self.prepare_archive_download()
        overrides.update({"AI_SUMMARY_LOCAL": "", "AI_SUMMARY_REF": "fix/example"})
        result = self.run_installer(overrides)
        self.assert_success(result)
        self.assertIn("/archive/fix/example.tar.gz", log.read_text())


if __name__ == "__main__":
    unittest.main()
