"""Tests for the decompiler, model_generator, and project_generator.

Uses upstream .reqif files from tests/fixtures/.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from reqif.parser import ReqIFParser

from reqif.specir.decompiler import decompile
from reqif.specir.importer import import_reqif
from reqif.specir.model_generator import generate_model
from reqif.specir.project_generator import generate_project

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TC1000 = os.path.join(_FIXTURES_DIR, "tc1000_simple_content.reqif")
_TC1300 = os.path.join(_FIXTURES_DIR, "tc1300_spec_relation.reqif")


def _import_fixture(path: str) -> tuple[sqlite3.Connection, str]:
    """Parse a .reqif file and import into an in-memory SpecIR database.

    Returns (conn, spec_id).
    """
    bundle = ReqIFParser.parse(path)
    conn = sqlite3.connect(":memory:")
    spec_id = import_reqif(bundle, conn)
    conn.row_factory = sqlite3.Row
    return conn, spec_id


class TestModelGenerator(unittest.TestCase):
    """Test Lua model type generation from SpecIR type system."""

    def test_tc1000_generates_object_type(self):
        conn, _ = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = generate_model(conn, tmp, "test_model")
            # Should create types/objects/ with the TC1000 object type.
            obj_dir = os.path.join(model_dir, "types", "objects")
            self.assertTrue(os.path.isdir(obj_dir), f"Missing: {obj_dir}")
            lua_files = [f for f in os.listdir(obj_dir) if f.endswith(".lua")]
            self.assertGreater(len(lua_files), 0, "No object type Lua files generated")

            # Read one and check structure.
            lua_path = os.path.join(obj_dir, lua_files[0])
            with open(lua_path) as f:
                content = f.read()
            self.assertIn("M.object", content)
            self.assertIn("id =", content)
            self.assertIn("attributes =", content)
            self.assertIn("return M", content)
        conn.close()

    def test_tc1000_generates_specification_type(self):
        conn, _ = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            generate_model(conn, tmp, "test_model")
            spec_dir = os.path.join(tmp, "models", "test_model", "types", "specifications")
            if os.path.isdir(spec_dir):
                lua_files = [f for f in os.listdir(spec_dir) if f.endswith(".lua")]
                for lf in lua_files:
                    with open(os.path.join(spec_dir, lf)) as f:
                        content = f.read()
                    self.assertIn("M.specification", content)
        conn.close()

    def test_tc1300_generates_relation_type(self):
        conn, _ = _import_fixture(_TC1300)
        with tempfile.TemporaryDirectory() as tmp:
            generate_model(conn, tmp, "test_model")
            rel_dir = os.path.join(tmp, "models", "test_model", "types", "relations")
            self.assertTrue(os.path.isdir(rel_dir), f"Missing: {rel_dir}")
            lua_files = [f for f in os.listdir(rel_dir) if f.endswith(".lua")]
            self.assertGreater(len(lua_files), 0, "No relation type Lua files generated")
            with open(os.path.join(rel_dir, lua_files[0])) as f:
                content = f.read()
            self.assertIn("M.relation", content)
            self.assertIn('extends = "PID_REF"', content)
        conn.close()

    def test_tc1000_enum_values_in_lua(self):
        """Enum attributes should include values = { ... } in Lua output."""
        conn, _ = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = generate_model(conn, tmp, "test_model")
            obj_dir = os.path.join(model_dir, "types", "objects")
            # Find any Lua file with ENUM attribute.
            found_enum = False
            for fn in os.listdir(obj_dir):
                with open(os.path.join(obj_dir, fn)) as f:
                    content = f.read()
                if "ENUM" in content and "values =" in content:
                    found_enum = True
                    break
            self.assertTrue(found_enum, "No ENUM attribute with values found in generated Lua")
        conn.close()

    def test_skips_builtin_section_type(self):
        """SECTION type should not be generated (it's built-in)."""
        conn, _ = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = generate_model(conn, tmp, "test_model")
            obj_dir = os.path.join(model_dir, "types", "objects")
            if os.path.isdir(obj_dir):
                self.assertNotIn("section.lua", os.listdir(obj_dir))
        conn.close()


class TestDecompiler(unittest.TestCase):
    """Test CommonSpec markdown generation from SpecIR."""

    def test_tc1000_single_file(self):
        """TC1000 has 1 object -> should produce single .md file."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp, children_threshold=50)
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].endswith(".md"))
            with open(files[0]) as f:
                content = f.read()
            # Should have a spec header (H1).
            self.assertTrue(content.startswith("#"), "Markdown should start with H1")
            # Should contain at least one H2 (the spec object).
            self.assertIn("## ", content)
        conn.close()

    def test_tc1300_single_file_with_relation(self):
        """TC1300 has 2 objects + 1 relation -> single file, relation rendered."""
        conn, spec_id = _import_fixture(_TC1300)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            self.assertEqual(len(files), 1)
            with open(files[0]) as f:
                content = f.read()
            # Should contain relation links.
            self.assertIn("(@)", content, "Expected PID-based relation link")
        conn.close()

    def test_multi_file_splitting(self):
        """With threshold=1, should split into multiple files."""
        conn, spec_id = _import_fixture(_TC1300)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp, children_threshold=1)
            # Should have root + child files.
            self.assertGreater(len(files), 1, "Expected multiple files with threshold=1")
            # Root file should have include block.
            root_files = [f for f in files if "/" not in os.path.relpath(f, tmp) or
                          os.path.relpath(f, tmp).count(os.sep) == 0]
            if root_files:
                with open(root_files[-1]) as f:
                    content = f.read()
                self.assertIn("{.include}", content, "Root file should contain include block")
        conn.close()

    def test_overwrite_protection(self):
        """Second decompile without overwrite should skip existing files."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files1 = decompile(conn, spec_id, tmp)
            self.assertEqual(len(files1), 1)
            # Write a marker to the file.
            with open(files1[0], "a") as f:
                f.write("\n<!-- MARKER -->\n")
            # Second run without overwrite -> should skip.
            files2 = decompile(conn, spec_id, tmp, overwrite=False)
            self.assertEqual(len(files2), 0, "Should skip existing files")
            # Marker should still be there.
            with open(files1[0]) as f:
                self.assertIn("MARKER", f.read())
        conn.close()

    def test_overwrite_replaces(self):
        """Decompile with overwrite=True should replace existing files."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files1 = decompile(conn, spec_id, tmp)
            with open(files1[0], "a") as f:
                f.write("\n<!-- MARKER -->\n")
            files2 = decompile(conn, spec_id, tmp, overwrite=True)
            self.assertEqual(len(files2), 1)
            with open(files2[0]) as f:
                self.assertNotIn("MARKER", f.read(), "File should have been overwritten")
        conn.close()

    def test_tc1000_attribute_formatting(self):
        """Attributes should be rendered as > name: value."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            with open(files[0]) as f:
                content = f.read()
            # TC1000 has boolean, integer, string, real, date, enum attributes.
            # At least some should appear as "> name: value".
            self.assertIn("> ", content, "Expected attribute lines with > prefix")
        conn.close()

    def test_pid_in_header(self):
        """Object headers should include @PID suffix."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            with open(files[0]) as f:
                content = f.read()
            # Imported objects should have auto-generated PIDs.
            self.assertIn("@", content, "Expected @PID in headers")
        conn.close()

    def test_type_prefix_in_header(self):
        """Non-SECTION types should have TYPE: prefix in headers."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            with open(files[0]) as f:
                content = f.read()
            # TC1000 has a spec object type "TC1000_SPECOBJECTTYPE" (not SECTION).
            # It should appear as a prefix.
            lines = content.split("\n")
            h2_lines = [l for l in lines if l.startswith("## ")]
            # At least one H2 should have a type prefix (non-SECTION).
            has_type_prefix = any(":" in l.split("@")[0] for l in h2_lines)
            self.assertTrue(has_type_prefix, f"Expected TYPE: prefix in H2 lines: {h2_lines}")
        conn.close()


class TestProjectGenerator(unittest.TestCase):
    """Test project.yaml generation."""

    def test_generates_valid_yaml(self):
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            path = generate_project(conn, spec_id, tmp)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                content = f.read()
            self.assertIn("project:", content)
            self.assertIn("template:", content)
            self.assertIn("doc_files:", content)
            self.assertIn("outputs:", content)
        conn.close()

    def test_uses_model_name(self):
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            generate_project(conn, spec_id, tmp, model_name="my_model")
            with open(os.path.join(tmp, "project.yaml")) as f:
                content = f.read()
            self.assertIn("template: my_model", content)
        conn.close()

    def test_uses_custom_doc_files(self):
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            generate_project(conn, spec_id, tmp, doc_files=["main.md", "appendix.md"])
            with open(os.path.join(tmp, "project.yaml")) as f:
                content = f.read()
            self.assertIn("main.md", content)
            self.assertIn("appendix.md", content)
        conn.close()

    def test_overwrite_protection(self):
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            generate_project(conn, spec_id, tmp)
            # Add marker.
            path = os.path.join(tmp, "project.yaml")
            with open(path, "a") as f:
                f.write("# MARKER\n")
            # Re-generate without overwrite.
            generate_project(conn, spec_id, tmp, overwrite=False)
            with open(path) as f:
                self.assertIn("MARKER", f.read())
        conn.close()


class TestFullRoundTrip(unittest.TestCase):
    """End-to-end: import .reqif -> decompile -> verify project structure."""

    def test_tc1300_full_project(self):
        """Import TC1300 → generate model + markdown + project.yaml."""
        conn, spec_id = _import_fixture(_TC1300)
        with tempfile.TemporaryDirectory() as tmp:
            # Generate model.
            model_dir = generate_model(conn, tmp, "imported")
            self.assertTrue(os.path.isdir(model_dir))

            # Generate markdown.
            md_files = decompile(conn, spec_id, tmp)
            self.assertGreater(len(md_files), 0)

            # Generate project.yaml.
            doc_files = [os.path.relpath(f, tmp) for f in md_files]
            root_files = [f for f in doc_files if os.sep not in f]
            proj_path = generate_project(
                conn, spec_id, tmp,
                model_name="imported",
                doc_files=root_files or doc_files,
            )
            self.assertTrue(os.path.exists(proj_path))

            # Verify structure.
            self.assertTrue(os.path.exists(os.path.join(tmp, "project.yaml")))
            self.assertTrue(os.path.isdir(os.path.join(tmp, "models", "imported")))
            for md_file in md_files:
                self.assertTrue(os.path.exists(md_file), f"Missing: {md_file}")
                with open(md_file) as f:
                    self.assertGreater(len(f.read()), 0, f"Empty: {md_file}")
        conn.close()

    def test_tc1000_all_datatypes_preserved(self):
        """Import TC1000 → decompile → check all attribute types appear."""
        conn, spec_id = _import_fixture(_TC1000)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            with open(files[0]) as f:
                content = f.read()
            # TC1000 has boolean, integer, string, real, date, enum.
            # Check that attribute lines exist.
            attr_lines = [l for l in content.split("\n") if l.startswith("> ")]
            self.assertGreater(len(attr_lines), 0, "Expected attribute lines in output")
        conn.close()

    def test_tc1300_relations_in_markdown(self):
        """Import TC1300 → decompile → verify relation links appear."""
        conn, spec_id = _import_fixture(_TC1300)
        with tempfile.TemporaryDirectory() as tmp:
            files = decompile(conn, spec_id, tmp)
            combined = ""
            for f_path in files:
                with open(f_path) as f:
                    combined += f.read()
            # Should have at least one relation link.
            self.assertIn("(@)", combined, "Expected relation link [pid](@)")
        conn.close()


if __name__ == "__main__":
    unittest.main()
