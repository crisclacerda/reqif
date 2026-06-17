"""Interop tests for exporting real SpecCompiler ``specir.db`` files.

These tests keep the integration boundary at the database:

* SpecCompiler is used only to build a minimal ``sw_docs`` project into
  ``build/specir.db``.
* ReqIF export, parse, and re-import are performed by this package.
* When StrictDoc is installed, the exported ReqIF is also decoded through its
  ReqIF importer into SDoc.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reqif.parser import ReqIFParser


def _find_speccompiler_home() -> Path | None:
    env_home = os.environ.get("SPECCOMPILER_HOME")
    if env_home:
        path = Path(env_home).resolve()
        if (path / "dist" / "bin" / "speccompiler-core").is_file():
            return path

    repo_root = Path(__file__).resolve().parents[3]
    sibling = repo_root.parent / "SpecCompiler"
    if (sibling / "dist" / "bin" / "speccompiler-core").is_file():
        return sibling.resolve()
    return None


def _write_minimal_sw_docs_project(project_dir: Path) -> Path:
    (project_dir / "project.yaml").write_text(
        """\
project:
  code: MINI
  name: Minimal SW Docs ReqIF Export

template: sw_docs
output_dir: build
logging:
  level: error
  format: console
  color: false

validation:
  traceability_hlr_allocation: warn
  traceability_hlr_to_vc: warn
  traceability_vc_to_hlr: warn

doc_files:
  - srs.md

outputs:
  - format: markdown
    path: md/{spec_id}.md
""",
        encoding="utf-8",
    )
    (project_dir / "srs.md").write_text(
        """\
# SRS: Minimal Software Requirements @SRS-MINI

> version: 1.0

> status: Draft

## HLR: Login Requirement @HLR-LOGIN

> status: Approved

> priority: High

> rationale: Users need protected access.

The system shall authenticate users before access is granted.

## VC: Login Verification @VC-LOGIN

> objective: Verify valid and invalid login attempts.

> verification_method: Test

> status: Draft

> traceability: [HLR-LOGIN](@)

Execute login attempts with valid and invalid credentials.
""",
        encoding="utf-8",
    )
    return project_dir / "project.yaml"


@unittest.skipUnless(
    _find_speccompiler_home() is not None,
    "sibling SpecCompiler checkout with dist/bin/speccompiler-core not found",
)
class TestSpecCompilerDBExport(unittest.TestCase):
    """Export a real sw_docs SpecIR DB without SpecCompiler-side ReqIF code."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.project_dir = Path(cls._tmp.name)
        cls.speccompiler_home = _find_speccompiler_home()
        assert cls.speccompiler_home is not None

        project_file = _write_minimal_sw_docs_project(cls.project_dir)
        wrapper = cls.speccompiler_home / "dist" / "bin" / "speccompiler-core"
        env = {
            **os.environ,
            "SPECCOMPILER_HOME": str(cls.speccompiler_home),
        }
        result = subprocess.run(
            [str(wrapper), "build", str(project_file)],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        if result.returncode != 0:
            raise AssertionError(
                "SpecCompiler minimal sw_docs build failed\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )

        cls.db_path = cls.project_dir / "build" / "specir.db"
        if not cls.db_path.is_file():
            raise AssertionError(f"SpecCompiler did not create {cls.db_path}")

        cls.reqif_path = cls.project_dir / "export.reqif"
        export_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "reqif.specir",
                "export",
                "--db",
                str(cls.db_path),
                "--output",
                str(cls.reqif_path),
                "--spec-id",
                "srs",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if export_result.returncode != 0:
            raise AssertionError(
                "reqif.specir CLI export failed\n"
                f"stdout:\n{export_result.stdout}\n\nstderr:\n{export_result.stderr}"
            )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_exported_reqif_parses_with_reqif_library(self):
        bundle = ReqIFParser.parse(str(self.reqif_path))
        self.assertFalse(bundle.exceptions)
        content = bundle.core_content.req_if_content
        self.assertEqual(len(content.spec_objects), 2)
        self.assertEqual(len(content.spec_relations), 1)

        object_names = {obj.long_name for obj in content.spec_objects}
        self.assertIn("Login Requirement", object_names)
        self.assertIn("Login Verification", object_names)

    def test_exported_reqif_imports_back_to_specir_with_cli(self):
        imported_db = self.project_dir / "roundtrip.db"
        import_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "reqif.specir",
                "import",
                "--input",
                str(self.reqif_path),
                "--db",
                str(imported_db),
                "--spec-id",
                "roundtrip",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            import_result.returncode, 0,
            "reqif.specir CLI import failed\n"
            f"stdout:\n{import_result.stdout}\nstderr:\n{import_result.stderr}",
        )

        conn = sqlite3.connect(imported_db)
        try:
            conn.row_factory = sqlite3.Row
            objects = [
                dict(row)
                for row in conn.execute(
                    "SELECT pid, title_text FROM spec_objects "
                    "WHERE specification_ref = ? ORDER BY file_seq",
                    ("roundtrip",),
                )
            ]
            relations = [
                dict(row)
                for row in conn.execute(
                    "SELECT type_ref, source_object_id, target_object_id "
                    "FROM spec_relations WHERE specification_ref = ?",
                    ("roundtrip",),
                )
            ]
        finally:
            conn.close()

        self.assertEqual(
            objects,
            [
                {"pid": "HLR-LOGIN", "title_text": "Login Requirement"},
                {"pid": "VC-LOGIN", "title_text": "Login Verification"},
            ],
        )
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]["type_ref"], "VERIFIES")
        self.assertEqual(relations[0]["source_object_id"], 2)
        self.assertEqual(relations[0]["target_object_id"], 1)

    def test_exported_reqif_decodes_to_strictdoc_sdoc_when_available(self):
        if shutil.which("strictdoc") is None:
            self.skipTest("strictdoc CLI not found")

        out_dir = self.project_dir / "strictdoc-out"
        result = subprocess.run(
            [
                "strictdoc",
                "import",
                "reqif",
                "p01_sdoc",
                str(self.reqif_path),
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            f"strictdoc import failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

        sdoc_files = list(out_dir.rglob("*.sdoc"))
        self.assertEqual(len(sdoc_files), 1)
        content = sdoc_files[0].read_text(encoding="utf-8")
        self.assertIn("UID: HLR-LOGIN", content)
        self.assertIn("UID: VC-LOGIN", content)
        self.assertIn("The system shall authenticate users", content)
        self.assertIn("VALUE: HLR-LOGIN", content)
