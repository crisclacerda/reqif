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

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_TC1300 = _FIXTURES_DIR / "tc1300_spec_relation.reqif"


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


def _find_model_checkout(model_name: str, style_name: str) -> Path | None:
    env_home = os.environ.get(f"SPECC_{model_name.upper().replace('-', '_')}_HOME")
    if env_home:
        path = Path(env_home).resolve()
        if (path / "model.yaml").is_file() and (path / "styles" / style_name).is_dir():
            return path

    repo_root = Path(__file__).resolve().parents[3]
    sibling = repo_root.parent / f"specc-{model_name}"
    if (sibling / "model.yaml").is_file() and (sibling / "styles" / style_name).is_dir():
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


def _write_multi_spec_sw_docs_project(project_dir: Path) -> Path:
    """Write an sw_docs project with three specifications (SRS, SDD, SVC).

    Relations span specifications: the LLR in the SDD traces to the HLR in the
    SRS, and the VC in the SVC verifies that same HLR.  These cross-spec links
    are the point of the round-trip test -- a per-specification export/import
    silently drops them.
    """
    (project_dir / "project.yaml").write_text(
        """\
project:
  code: SWMULTI
  name: Multi-Spec SW Docs RoundTrip

template: sw_docs
output_dir: build
logging:
  level: error
  format: console
  color: false

validation:
  traceability_hlr_allocation: warn
  traceability_hlr_missing_allocation: warn
  traceability_hlr_to_vc: warn
  traceability_hlr_missing_vc: warn
  traceability_vc_to_hlr: warn
  traceability_vc_missing_hlr: warn
  traceability_llr_to_vc: warn
  traceability_llr_missing_vc: warn

doc_files:
  - srs.md
  - sdd.md
  - svc.md

outputs:
  - format: markdown
    path: md/{spec_id}.md
""",
        encoding="utf-8",
    )
    (project_dir / "srs.md").write_text(
        """\
# SRS: Minimal Requirements @SRS-MULTI

> version: 1.0

> status: Draft

## HLR: Login Requirement @HLR-LOGIN

> status: Approved

> priority: High

> rationale: Users need protected access.

The system shall authenticate users before access is granted.
""",
        encoding="utf-8",
    )
    (project_dir / "sdd.md").write_text(
        """\
# SDD: Minimal Design @SDD-MULTI

> status: Draft

## LLR: Login Design @LLR-LOGIN

> status: Approved

> verification_method: Test

> rationale: OAuth2 chosen for interoperability.

> traceability: [HLR-LOGIN](@)

The login module shall validate credentials against the identity provider.
""",
        encoding="utf-8",
    )
    (project_dir / "svc.md").write_text(
        """\
# SVC: Minimal Verification @SVC-MULTI

> status: Draft

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


@unittest.skipUnless(
    _find_speccompiler_home() is not None,
    "sibling SpecCompiler checkout with dist/bin/speccompiler-core not found",
)
class TestMultiSpecSwDocsRoundTrip(unittest.TestCase):
    """Round-trip a three-specification sw_docs project (SRS + SDD + SVC).

    One generic path handles single and multiple specifications; here it must
    preserve the SDD->SRS and SVC->SRS relations that cross specification
    boundaries through ``export --all`` and re-import.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.project_dir = Path(cls._tmp.name)
        cls.speccompiler_home = _find_speccompiler_home()
        assert cls.speccompiler_home is not None

        project_file = _write_multi_spec_sw_docs_project(cls.project_dir)
        wrapper = cls.speccompiler_home / "dist" / "bin" / "speccompiler-core"
        env = {**os.environ, "SPECCOMPILER_HOME": str(cls.speccompiler_home)}
        result = subprocess.run(
            [str(wrapper), "build", str(project_file)],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        if result.returncode != 0:
            raise AssertionError(
                "SpecCompiler multi-spec sw_docs build failed\n"
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
                "--all",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if export_result.returncode != 0:
            raise AssertionError(
                "reqif.specir CLI export --all failed\n"
                f"stdout:\n{export_result.stdout}\n\nstderr:\n{export_result.stderr}"
            )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_build_creates_three_specifications(self):
        conn = sqlite3.connect(self.db_path)
        try:
            specs = [
                r[0]
                for r in conn.execute(
                    "SELECT identifier FROM specifications ORDER BY identifier"
                )
            ]
        finally:
            conn.close()
        self.assertEqual(specs, ["sdd", "srs", "svc"])

    def test_exported_reqif_has_three_specifications(self):
        bundle = ReqIFParser.parse(str(self.reqif_path))
        self.assertFalse(bundle.exceptions)
        content = bundle.core_content.req_if_content
        self.assertEqual(len(content.specifications), 3)
        self.assertEqual(
            sorted(spec.long_name for spec in content.specifications),
            ["Minimal Design", "Minimal Requirements", "Minimal Verification"],
        )

    def test_cross_specification_relations_survive_roundtrip(self):
        imported_db = self.project_dir / "roundtrip.db"
        if imported_db.exists():
            imported_db.unlink()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "reqif.specir",
                "import",
                "--input",
                str(self.reqif_path),
                "--db",
                str(imported_db),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            f"import failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

        conn = sqlite3.connect(imported_db)
        conn.row_factory = sqlite3.Row
        try:
            rows = [
                dict(r)
                for r in conn.execute(
                    "SELECT r.type_ref, s1.pid AS src, s2.pid AS tgt, "
                    "       s1.specification_ref AS src_spec, "
                    "       s2.specification_ref AS tgt_spec "
                    "FROM spec_relations r "
                    "JOIN spec_objects s1 ON s1.id = r.source_object_id "
                    "JOIN spec_objects s2 ON s2.id = r.target_object_id"
                )
            ]
        finally:
            conn.close()

        by_endpoints = {(r["src"], r["tgt"]): r for r in rows}
        # VC (in SVC) verifies HLR (in SRS); LLR (in SDD) references HLR (in
        # SRS).  Both relations cross specification boundaries.
        self.assertIn(("VC-LOGIN", "HLR-LOGIN"), by_endpoints)
        self.assertIn(("LLR-LOGIN", "HLR-LOGIN"), by_endpoints)
        for endpoints in (("VC-LOGIN", "HLR-LOGIN"), ("LLR-LOGIN", "HLR-LOGIN")):
            rel = by_endpoints[endpoints]
            self.assertNotEqual(
                rel["src_spec"], rel["tgt_spec"],
                f"relation {endpoints} should span two specifications",
            )

    def test_import_decompile_all_regenerates_three_docs(self):
        out_dir = self.project_dir / "decompiled"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "reqif.specir",
                "import-decompile",
                "--input",
                str(self.reqif_path),
                "--output-dir",
                str(out_dir),
                "--all",
                "--overwrite",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            "import-decompile --all failed\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        md_files = sorted(f.name for f in out_dir.glob("*.md"))
        self.assertEqual(len(md_files), 3, f"expected 3 root docs, got {md_files}")


@unittest.skipUnless(
    _find_speccompiler_home() is not None,
    "sibling SpecCompiler checkout not found",
)
class TestReqIFToBaseModelDocx(unittest.TestCase):
    """Import a bundled ReqIF fixture and build it through existing models."""

    def _build_reqif_fixture_with_base_model(
        self,
        model_name: str,
        style_name: str,
        checkout: Path,
    ) -> None:
        speccompiler_home = _find_speccompiler_home()
        assert speccompiler_home is not None

        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            generated_model = f"imported_{model_name.replace('-', '_')}"
            models_dir = project_dir / "models"
            models_dir.mkdir()
            (project_dir / "src").symlink_to(
                speccompiler_home / "src",
                target_is_directory=True,
            )
            (models_dir / "default").symlink_to(
                speccompiler_home / "models" / "default",
                target_is_directory=True,
            )
            (models_dir / model_name).symlink_to(
                checkout,
                target_is_directory=True,
            )

            import_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "reqif.specir",
                    "import-decompile",
                    "--input",
                    str(_TC1300),
                    "--output-dir",
                    str(project_dir),
                    "--model-name",
                    generated_model,
                    "--base-model",
                    model_name,
                    "--style",
                    style_name,
                    "--overwrite",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                import_result.returncode, 0,
                "reqif.specir import-decompile failed\n"
                f"stdout:\n{import_result.stdout}\nstderr:\n{import_result.stderr}",
            )

            wrapper = speccompiler_home / "dist" / "bin" / "speccompiler-core"
            env = {
                **os.environ,
                "SPECCOMPILER_HOME": str(project_dir),
            }
            build_result = subprocess.run(
                [str(wrapper), "build", str(project_dir / "project.yaml")],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            combined_output = build_result.stdout + build_result.stderr
            self.assertEqual(
                build_result.returncode, 0,
                f"SpecCompiler {model_name} build failed\n"
                f"stdout:\n{build_result.stdout}\nstderr:\n{build_result.stderr}",
            )
            self.assertNotIn("Unknown type", combined_output)
            self.assertNotIn("Failed to generate docx", combined_output)
            self.assertIn("reference.docx rebuilt successfully", combined_output)
            self.assertIn(
                f"[DOCX-POST] Loaded post-processor for template: {generated_model}",
                combined_output,
            )

            docx_path = project_dir / "build" / "docx" / "id-tc1300-specification.docx"
            self.assertTrue(docx_path.is_file(), f"Missing DOCX: {docx_path}")
            self.assertGreater(docx_path.stat().st_size, 3000)

            conn = sqlite3.connect(project_dir / "build" / "specir.db")
            try:
                object_types = {
                    r[0] for r in conn.execute("SELECT DISTINCT type_ref FROM spec_objects")
                }
                spec_types = {
                    r[0] for r in conn.execute("SELECT DISTINCT type_ref FROM specifications")
                }
            finally:
                conn.close()

            self.assertIn("TC1300_SPECOBJECTTYPE", object_types)
            self.assertIn("TC1300_SPECIFICATIONTYPE", spec_types)

    def test_reqif_fixture_builds_with_existing_base_models(self):
        cases = [
            ("abnt", "academico"),
            ("emb", "emb-report"),
        ]
        for model_name, style_name in cases:
            checkout = _find_model_checkout(model_name, style_name)
            if checkout is None:
                self.skipTest(f"specc-{model_name} checkout not found")
            with self.subTest(model_name=model_name, style_name=style_name):
                self._build_reqif_fixture_with_base_model(
                    model_name,
                    style_name,
                    checkout,
                )
