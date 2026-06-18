"""CLI integration tests for reqif.specir.

Tests the command-line interface end-to-end via subprocess.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree

from reqif.specir.tests.test_specir import _make_multi_spec_bundle
from reqif.unparser import ReqIFUnparser

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

            conn = sqlite3.connect(db)
            try:
                object_count = conn.execute(
                    "SELECT COUNT(*) FROM spec_objects"
                ).fetchone()[0]
                relation_count = conn.execute(
                    "SELECT COUNT(*) FROM spec_relations"
                ).fetchone()[0]
                titles = [
                    r[0] for r in conn.execute(
                        "SELECT title_text FROM spec_objects ORDER BY file_seq"
                    ).fetchall()
                ]
            finally:
                conn.close()
            self.assertEqual(object_count, 2)
            self.assertEqual(relation_count, 1)
            self.assertEqual(
                titles,
                ["ID_TC1300_SpecObject1", "ID_TC1300_SpecObject2"],
            )

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

    def test_multi_spec_requires_all_for_bundle_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            reqif_path = os.path.join(tmp, "multi.reqif")
            db = os.path.join(tmp, "multi.db")
            exported = os.path.join(tmp, "exported.reqif")
            project_dir = os.path.join(tmp, "project")

            with open(reqif_path, "w", encoding="utf-8") as f:
                f.write(ReqIFUnparser.unparse(_make_multi_spec_bundle()))

            r = _run(["import", "--input", reqif_path, "--db", db])
            self.assertEqual(r.returncode, 0, f"Import failed: {r.stderr}")
            self.assertIn("Specifications: test-sdd, test-srs", r.stdout)

            conn = sqlite3.connect(db)
            try:
                specs = [
                    row[0] for row in conn.execute(
                        "SELECT identifier FROM specifications ORDER BY identifier"
                    )
                ]
            finally:
                conn.close()
            self.assertEqual(specs, ["test-sdd", "test-srs"])

            r = _run(["export", "--db", db, "--output", exported])
            self.assertEqual(r.returncode, 2)
            self.assertIn("multiple specifications", r.stderr)

            r = _run(["export", "--db", db, "--output", exported, "--all"])
            self.assertEqual(r.returncode, 0, f"Export --all failed: {r.stderr}")
            bundle_root = ElementTree.fromstring(open(exported, encoding="utf-8").read())
            self.assertIsNotNone(bundle_root)

            r = _run([
                "import-decompile",
                "--input", reqif_path,
                "--output-dir", project_dir,
                "--overwrite",
            ])
            self.assertEqual(r.returncode, 2)
            self.assertIn("Use --all", r.stderr)

            r = _run([
                "import-decompile",
                "--input", reqif_path,
                "--output-dir", project_dir,
                "--all",
                "--overwrite",
            ])
            self.assertEqual(r.returncode, 0, f"import-decompile --all failed: {r.stderr}")
            md_files = [f for f in os.listdir(project_dir) if f.endswith(".md")]
            self.assertEqual(sorted(md_files), ["test-sdd.md", "test-srs.md"])
            with open(os.path.join(project_dir, "project.yaml"), encoding="utf-8") as f:
                project_yaml = f.read()
            self.assertIn("  - test-sdd.md", project_yaml)
            self.assertIn("  - test-srs.md", project_yaml)
            self.assertIn("path: docx/{spec_id}.docx", project_yaml)


if __name__ == "__main__":
    unittest.main()
