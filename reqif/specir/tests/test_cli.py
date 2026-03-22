"""CLI integration tests for reqif.specir.

Tests the command-line interface end-to-end via subprocess.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TC1000 = os.path.join(_FIXTURES_DIR, "tc1000_simple_content.reqif")
_TC1300 = os.path.join(_FIXTURES_DIR, "tc1300_spec_relation.reqif")
_PYTHONPATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _run(args, **kwargs):
    env = {**os.environ, "PYTHONPATH": _PYTHONPATH}
    return subprocess.run(
        ["python3", "-m", "reqif.specir"] + args,
        capture_output=True, text=True, env=env, **kwargs,
    )


class TestCLI(unittest.TestCase):

    def test_all_subcommands_have_help(self):
        for cmd in ("import", "export", "decompile", "import-decompile"):
            r = _run([cmd, "--help"])
            self.assertEqual(r.returncode, 0, f"{cmd} --help failed")
            self.assertIn("--", r.stdout, f"{cmd} --help missing options")

    def test_import_then_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            out = os.path.join(tmp, "exported.reqif")
            r = _run(["import", "--input", _TC1300, "--db", db])
            self.assertEqual(r.returncode, 0, f"Import failed: {r.stderr}")
            r = _run(["export", "--db", db, "--output", out])
            self.assertEqual(r.returncode, 0, f"Export failed: {r.stderr}")
            with open(out) as f:
                root = ElementTree.fromstring(f.read())
            self.assertIsNotNone(root)

    def test_import_decompile(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _run(["import-decompile", "--input", _TC1300, "--output-dir", tmp, "--overwrite"])
            self.assertEqual(r.returncode, 0, f"import-decompile failed: {r.stderr}")
            self.assertTrue(os.path.exists(os.path.join(tmp, "project.yaml")))
            self.assertTrue(os.path.isdir(os.path.join(tmp, "models", "imported")))
            md_files = [f for f in os.listdir(tmp) if f.endswith(".md")]
            self.assertGreater(len(md_files), 0)

    def test_decompile_two_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            project_dir = os.path.join(tmp, "project")
            os.makedirs(project_dir)
            r = _run(["import", "--input", _TC1000, "--db", db])
            self.assertEqual(r.returncode, 0, f"Import failed: {r.stderr}")
            r = _run(["decompile", "--db", db, "--output-dir", project_dir, "--overwrite"])
            self.assertEqual(r.returncode, 0, f"Decompile failed: {r.stderr}")
            self.assertTrue(os.path.exists(os.path.join(project_dir, "project.yaml")))


if __name__ == "__main__":
    unittest.main()
