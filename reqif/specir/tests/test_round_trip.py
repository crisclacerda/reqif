"""ReqIF round-trip tests and CommonSpec output validation.

Tests the full lifecycle using upstream .reqif fixtures:
  - ReqIF → import → SpecIR → export → ReqIF  (round-trip fidelity)
  - ReqIF → import → SpecIR → decompile → CommonSpec  (output validation)

Self-contained — uses only the bundled tc1000/tc1300 fixtures.
"""
from __future__ import annotations

import os
import re
import sqlite3
import tempfile
import unittest
from xml.etree import ElementTree

from reqif.parser import ReqIFParser
from reqif.unparser import ReqIFUnparser

from reqif.specir.decompiler import decompile
from reqif.specir.exporter import export_reqif
from reqif.specir.importer import import_reqif

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TC1000 = os.path.join(_FIXTURES_DIR, "tc1000_simple_content.reqif")
_TC1300 = os.path.join(_FIXTURES_DIR, "tc1300_spec_relation.reqif")


def _import_fixture(path):
    bundle = ReqIFParser.parse(path)
    conn = sqlite3.connect(":memory:")
    spec_id = import_reqif(bundle, conn)
    conn.row_factory = sqlite3.Row
    return conn, spec_id


def _export_xml(conn, spec_id):
    return ReqIFUnparser.unparse(export_reqif(conn, spec_id))


def _count_xml(xml, tag_suffix):
    root = ElementTree.fromstring(xml)
    return sum(1 for el in root.iter() if el.tag.endswith(tag_suffix))


def _decompile_single(path, **kwargs):
    """Import fixture and decompile to a temp dir. Returns (content, conn)."""
    conn, spec_id = _import_fixture(path)
    tmp = tempfile.mkdtemp()
    files = decompile(conn, spec_id, tmp, overwrite=True, **kwargs)
    contents = {}
    for f in files:
        with open(f) as fh:
            contents[os.path.relpath(f, tmp)] = fh.read()
    return contents, files, tmp, conn


# ─────────────────────────────────────────────────────────────────────────
# ReqIF round-trip
# ─────────────────────────────────────────────────────────────────────────

class TestReqIFRoundTrip(unittest.TestCase):
    """Import → export → re-parse round-trip."""

    def test_tc1000_produces_valid_reqif(self):
        conn, spec_id = _import_fixture(_TC1000)
        xml = _export_xml(conn, spec_id)
        conn.close()
        with tempfile.NamedTemporaryFile(suffix=".reqif", mode="w", delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                b2 = ReqIFParser.parse(f.name)
                self.assertFalse(b2.exceptions, f"Parse errors: {b2.exceptions}")
            finally:
                os.unlink(f.name)

    def test_tc1000_preserves_object_count(self):
        conn, spec_id = _import_fixture(_TC1000)
        n = conn.execute(
            "SELECT COUNT(*) FROM spec_objects WHERE specification_ref = ?", (spec_id,),
        ).fetchone()[0]
        xml = _export_xml(conn, spec_id)
        conn.close()
        self.assertGreater(n, 0)
        self.assertEqual(_count_xml(xml, "SPEC-OBJECT"), n)

    def test_tc1000_preserves_titles(self):
        conn, spec_id = _import_fixture(_TC1000)
        titles = sorted(
            r[0] for r in conn.execute(
                "SELECT title_text FROM spec_objects WHERE specification_ref = ?", (spec_id,),
            ).fetchall()
        )
        xml = _export_xml(conn, spec_id)
        conn.close()
        with tempfile.NamedTemporaryFile(suffix=".reqif", mode="w", delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                b2 = ReqIFParser.parse(f.name)
                conn2 = sqlite3.connect(":memory:")
                import_reqif(b2, conn2)
                conn2.row_factory = sqlite3.Row
                titles2 = sorted(
                    r["title_text"] for r in conn2.execute(
                        "SELECT title_text FROM spec_objects ORDER BY file_seq",
                    ).fetchall()
                )
                conn2.close()
                self.assertEqual(titles, titles2)
            finally:
                os.unlink(f.name)

    def test_tc1300_preserves_relations(self):
        conn, spec_id = _import_fixture(_TC1300)
        n = conn.execute(
            "SELECT COUNT(*) FROM spec_relations WHERE specification_ref = ?", (spec_id,),
        ).fetchone()[0]
        xml = _export_xml(conn, spec_id)
        conn.close()
        self.assertGreater(n, 0)
        self.assertEqual(_count_xml(xml, "SPEC-RELATION"), n)

    def test_tc1300_double_round_trip_stable(self):
        conn, spec_id = _import_fixture(_TC1300)
        xml1 = _export_xml(conn, spec_id)
        conn.close()
        with tempfile.NamedTemporaryFile(suffix=".reqif", mode="w", delete=False) as f:
            f.write(xml1)
            f.flush()
            try:
                b2 = ReqIFParser.parse(f.name)
                conn2 = sqlite3.connect(":memory:")
                sid2 = import_reqif(b2, conn2)
                conn2.row_factory = sqlite3.Row
                xml2 = _export_xml(conn2, sid2)
                conn2.close()
                self.assertEqual(
                    _count_xml(xml1, "SPEC-OBJECT"),
                    _count_xml(xml2, "SPEC-OBJECT"),
                )
                self.assertEqual(
                    _count_xml(xml1, "SPEC-RELATION"),
                    _count_xml(xml2, "SPEC-RELATION"),
                )
            finally:
                os.unlink(f.name)


# ─────────────────────────────────────────────────────────────────────────
# CommonSpec output — TC1000 attribute coverage
# ─────────────────────────────────────────────────────────────────────────

class TestCommonSpecTC1000(unittest.TestCase):
    """Validate generated CommonSpec from TC1000 (all attribute datatypes)."""

    @classmethod
    def setUpClass(cls):
        cls._contents, cls._files, cls._tmp, cls._conn = _decompile_single(_TC1000)
        assert len(cls._contents) == 1, f"Expected 1 file, got {len(cls._contents)}"
        cls.md = list(cls._contents.values())[0]

    @classmethod
    def tearDownClass(cls):
        cls._conn.close()
        import shutil
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_spec_header_is_h1(self):
        self.assertTrue(self.md.startswith("# "))

    def test_object_heading_format(self):
        """H2 should be: ## TYPE: Title @PID"""
        h2s = [l for l in self.md.split("\n") if l.startswith("## ")]
        self.assertGreater(len(h2s), 0)
        h2 = h2s[0]
        self.assertIn("TC1000_SPECOBJECTTYPE:", h2)
        self.assertRegex(h2, r"@\S+")

    def test_boolean_true_attr(self):
        self.assertIn("> TC1000T: true", self.md)

    def test_boolean_false_attr(self):
        self.assertIn("> TC1000F: false", self.md)

    def test_integer_attr(self):
        self.assertIn("> TC1000 Integer: 5000", self.md)

    def test_string_attr(self):
        self.assertIn("> TC1000 String: Plain", self.md)

    def test_real_attr(self):
        self.assertIn("> TC1000 Real: 1234.5", self.md)

    def test_date_attr(self):
        # Date value from fixture: 2002-05-30T09:30:10.000+06:00
        lines = [l for l in self.md.split("\n") if l.startswith("> TC1000 Date:")]
        self.assertGreater(len(lines), 0, "Expected date attribute line")
        self.assertIn("2002-05-30", lines[0])

    def test_enum_attr(self):
        self.assertIn("> TC1000 Enum: TC1000 Yellow", self.md)

    def test_attr_lines_use_blockquote_syntax(self):
        """All attribute lines should match > name: value."""
        attr_lines = [l for l in self.md.split("\n") if l.startswith("> ")]
        self.assertGreater(len(attr_lines), 0)
        for line in attr_lines:
            self.assertRegex(line, r"^> .+: .+")


# ─────────────────────────────────────────────────────────────────────────
# CommonSpec output — TC1300 relations and structure
# ─────────────────────────────────────────────────────────────────────────

class TestCommonSpecTC1300(unittest.TestCase):
    """Validate generated CommonSpec from TC1300 (relations)."""

    @classmethod
    def setUpClass(cls):
        cls._contents, cls._files, cls._tmp, cls._conn = _decompile_single(_TC1300)
        assert len(cls._contents) == 1
        cls.md = list(cls._contents.values())[0]

    @classmethod
    def tearDownClass(cls):
        cls._conn.close()
        import shutil
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_two_h2_headings(self):
        h2s = [l for l in self.md.split("\n") if l.startswith("## ")]
        self.assertEqual(len(h2s), 2)

    def test_relation_link_rendered(self):
        self.assertIn("[TC1300_SPECOBJECTTYPE-002](@)", self.md)

    def test_relation_target_is_valid_pid(self):
        """The relation target PID should appear as @PID in some heading."""
        pids_in_headings = set(re.findall(r"@(\S+)", self.md))
        # Extract target PIDs from relation links
        targets = re.findall(r"\[(\S+)\]\(@\)", self.md)
        for target in targets:
            self.assertIn(target, pids_in_headings, f"Relation target {target} not found in headings")

    def test_string_attrs(self):
        self.assertIn("> TC1300 String: Requirement 1", self.md)
        self.assertIn("> TC1300 String: Requirement 2", self.md)


class TestCommonSpecMultiFile(unittest.TestCase):
    """Validate multi-file output with include blocks."""

    @classmethod
    def setUpClass(cls):
        cls._contents, cls._files, cls._tmp, cls._conn = _decompile_single(
            _TC1300, children_threshold=1,
        )

    @classmethod
    def tearDownClass(cls):
        cls._conn.close()
        import shutil
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_more_than_one_file(self):
        self.assertGreater(len(self._contents), 1)

    def test_root_has_include_block(self):
        root_files = [k for k in self._contents if os.sep not in k and "/" not in k]
        self.assertGreater(len(root_files), 0)
        root_md = self._contents[root_files[0]]
        self.assertIn("{.include}", root_md)

    def test_include_filenames_match_children(self):
        root_files = [k for k in self._contents if os.sep not in k and "/" not in k]
        root_md = self._contents[root_files[0]]
        # Extract filenames from include block
        in_block = False
        includes = []
        for line in root_md.split("\n"):
            if "{.include}" in line:
                in_block = True
                continue
            if in_block:
                if line.startswith("```"):
                    break
                if line.strip():
                    includes.append(line.strip())
        # Each include should map to an actual child file
        child_keys = [k for k in self._contents if k not in root_files]
        for inc in includes:
            self.assertIn(inc, child_keys, f"Include {inc} not found in generated files")

    def test_child_files_start_with_heading(self):
        root_files = [k for k in self._contents if os.sep not in k and "/" not in k]
        for key, content in self._contents.items():
            if key in root_files:
                continue
            self.assertTrue(
                content.strip().startswith("##"),
                f"Child file {key} should start with ## heading",
            )


if __name__ == "__main__":
    unittest.main()
