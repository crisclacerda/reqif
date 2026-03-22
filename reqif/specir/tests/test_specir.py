"""Tests for the reqif.specir subpackage (import, export, round-trip)."""
from __future__ import annotations

import sqlite3
import unittest

from reqif.models.reqif_core_content import ReqIFCoreContent
from reqif.models.reqif_data_type import (
    ReqIFDataTypeDefinitionEnumeration,
    ReqIFDataTypeDefinitionString,
    ReqIFDataTypeDefinitionXHTML,
    ReqIFEnumValue,
)
from reqif.models.reqif_namespace_info import ReqIFNamespaceInfo
from reqif.models.reqif_req_if_content import ReqIFReqIFContent
from reqif.models.reqif_reqif_header import ReqIFReqIFHeader
from reqif.models.reqif_spec_hierarchy import ReqIFSpecHierarchy
from reqif.models.reqif_spec_object import ReqIFSpecObject, SpecObjectAttribute
from reqif.models.reqif_spec_object_type import (
    ReqIFSpecObjectType,
    SpecAttributeDefinition,
)
from reqif.models.reqif_spec_relation import ReqIFSpecRelation
from reqif.models.reqif_spec_relation_type import ReqIFSpecRelationType
from reqif.models.reqif_specification import ReqIFSpecification
from reqif.models.reqif_specification_type import ReqIFSpecificationType
from reqif.models.reqif_types import SpecObjectAttributeType
from reqif.object_lookup import ReqIFObjectLookup
from reqif.reqif_bundle import ReqIFBundle

from reqif.specir import export_reqif, import_reqif
from reqif.specir.id_map import IdMap, _stable_id
from reqif.specir.schema import ensure_schema
from reqif.specir.xhtml import from_reqif_xhtml, to_reqif_xhtml


def _make_in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _make_sample_bundle() -> ReqIFBundle:
    """Build a minimal ReqIFBundle with two objects and a relation."""
    dt_string = ReqIFDataTypeDefinitionString(
        identifier="DT-STRING", long_name="String", last_change="2024-01-01T00:00:00Z",
    )
    dt_xhtml = ReqIFDataTypeDefinitionXHTML(
        identifier="DT-XHTML", long_name="XHTML", last_change="2024-01-01T00:00:00Z",
    )
    dt_enum = ReqIFDataTypeDefinitionEnumeration(
        identifier="DT-STATUS",
        long_name="Status",
        last_change="2024-01-01T00:00:00Z",
        values=[
            ReqIFEnumValue.create(identifier="EV-DRAFT", key="draft"),
            ReqIFEnumValue.create(identifier="EV-APPROVED", key="approved"),
        ],
    )

    ad_fid = SpecAttributeDefinition.create(
        attribute_type=SpecObjectAttributeType.STRING,
        identifier="AD-FID",
        datatype_definition="DT-STRING",
        long_name="ReqIF.ForeignID",
    )
    ad_name = SpecAttributeDefinition.create(
        attribute_type=SpecObjectAttributeType.STRING,
        identifier="AD-NAME",
        datatype_definition="DT-STRING",
        long_name="ReqIF.Name",
    )
    ad_text = SpecAttributeDefinition.create(
        attribute_type=SpecObjectAttributeType.XHTML,
        identifier="AD-TEXT",
        datatype_definition="DT-XHTML",
        long_name="ReqIF.Text",
    )
    ad_status = SpecAttributeDefinition.create(
        attribute_type=SpecObjectAttributeType.ENUMERATION,
        identifier="AD-STATUS",
        datatype_definition="DT-STATUS",
        long_name="status",
    )

    obj_type = ReqIFSpecObjectType.create(
        identifier="SOT-HLR",
        long_name="HLR",
        last_change="2024-01-01T00:00:00Z",
        attribute_definitions=[ad_fid, ad_name, ad_text, ad_status],
    )
    rel_type = ReqIFSpecRelationType(
        identifier="SRT-TRACES",
        long_name="TRACES_TO",
        last_change="2024-01-01T00:00:00Z",
        is_self_closed=True,
    )
    spec_type = ReqIFSpecificationType(
        identifier="ST-SPEC",
        long_name="SRS",
        last_change="2024-01-01T00:00:00Z",
        spec_attributes=None,
        spec_attribute_map={},
        is_self_closed=True,
    )

    obj1 = ReqIFSpecObject(
        identifier="SO-1",
        spec_object_type="SOT-HLR",
        attributes=[
            SpecObjectAttribute(SpecObjectAttributeType.STRING, "AD-FID", "HLR-001"),
            SpecObjectAttribute(SpecObjectAttributeType.STRING, "AD-NAME", "First Requirement"),
            SpecObjectAttribute(SpecObjectAttributeType.XHTML, "AD-TEXT", "<xhtml:div>The system shall do X.</xhtml:div>"),
            SpecObjectAttribute(SpecObjectAttributeType.ENUMERATION, "AD-STATUS", ["EV-DRAFT"]),
        ],
        long_name="First Requirement",
        last_change="2024-01-01T00:00:00Z",
    )
    obj2 = ReqIFSpecObject(
        identifier="SO-2",
        spec_object_type="SOT-HLR",
        attributes=[
            SpecObjectAttribute(SpecObjectAttributeType.STRING, "AD-FID", "HLR-002"),
            SpecObjectAttribute(SpecObjectAttributeType.STRING, "AD-NAME", "Second Requirement"),
            SpecObjectAttribute(SpecObjectAttributeType.XHTML, "AD-TEXT", "<xhtml:div>The system shall do Y.</xhtml:div>"),
        ],
        long_name="Second Requirement",
        last_change="2024-01-01T00:00:00Z",
    )

    rel = ReqIFSpecRelation(
        identifier="SR-1",
        relation_type_ref="SRT-TRACES",
        source="SO-1",
        target="SO-2",
        last_change="2024-01-01T00:00:00Z",
    )

    hierarchy = [
        ReqIFSpecHierarchy(
            identifier="H-1",
            spec_object="SO-1",
            level=1,
            children=[],
            ref_then_children_order=True,
        ),
        ReqIFSpecHierarchy(
            identifier="H-2",
            spec_object="SO-2",
            level=1,
            children=[],
            ref_then_children_order=True,
        ),
    ]

    specification = ReqIFSpecification(
        identifier="SPEC-1",
        long_name="Test SRS",
        specification_type="ST-SPEC",
        children=hierarchy,
        last_change="2024-01-01T00:00:00Z",
    )

    content = ReqIFReqIFContent(
        data_types=[dt_string, dt_xhtml, dt_enum],
        spec_types=[obj_type, rel_type, spec_type],
        spec_objects=[obj1, obj2],
        spec_relations=[rel],
        specifications=[specification],
        spec_relation_groups=[],
    )

    return ReqIFBundle(
        namespace_info=ReqIFNamespaceInfo.create_default(),
        req_if_header=ReqIFReqIFHeader(
            identifier="HDR-1",
            creation_time="2024-01-01T00:00:00Z",
            repository_id="test",
            req_if_tool_id="test",
            req_if_version="1.0",
            source_tool_id="test",
            title="Test Bundle",
        ),
        core_content=ReqIFCoreContent(req_if_content=content),
        tool_extensions_tag_exists=False,
        lookup=ReqIFObjectLookup.empty(),
        exceptions=[],
    )


class TestSchema(unittest.TestCase):
    def test_ensure_schema_creates_tables(self):
        conn = _make_in_memory_db()
        ensure_schema(conn)
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected in (
            "spec_object_types", "spec_float_types", "spec_relation_types",
            "spec_view_types", "datatype_definitions", "spec_attribute_types",
            "enum_values", "specifications", "spec_objects", "spec_floats",
            "spec_relations", "spec_views", "spec_attribute_values",
        ):
            self.assertIn(expected, tables, f"Missing table: {expected}")
        conn.close()

    def test_ensure_schema_is_idempotent(self):
        conn = _make_in_memory_db()
        ensure_schema(conn)
        ensure_schema(conn)  # should not raise
        conn.close()


class TestIdMap(unittest.TestCase):
    def test_put_and_get(self):
        conn = _make_in_memory_db()
        m = IdMap(conn)
        m.put("spec_objects", "42", "SO-abc123")
        self.assertEqual(m.get_reqif_id("spec_objects", "42"), "SO-abc123")
        self.assertEqual(m.get_specir_id("SO-abc123"), ("spec_objects", "42"))
        conn.close()

    def test_ensure_generates_stable_id(self):
        conn = _make_in_memory_db()
        m = IdMap(conn)
        rid = m.ensure_reqif_id("spec_objects", "99", "SO")
        self.assertTrue(rid.startswith("_SO-"))
        # Same call returns same value.
        self.assertEqual(m.ensure_reqif_id("spec_objects", "99", "SO"), rid)
        conn.close()

    def test_ensure_returns_existing(self):
        conn = _make_in_memory_db()
        m = IdMap(conn)
        m.put("spec_objects", "1", "ORIGINAL-ID")
        # ensure should return the existing mapping, not generate a new one.
        self.assertEqual(m.ensure_reqif_id("spec_objects", "1", "SO"), "ORIGINAL-ID")
        conn.close()

    def test_stable_id_deterministic(self):
        self.assertEqual(_stable_id("X", "hello"), _stable_id("X", "hello"))
        self.assertNotEqual(_stable_id("X", "hello"), _stable_id("Y", "hello"))


class TestXhtml(unittest.TestCase):
    def test_to_reqif_xhtml_empty(self):
        result = to_reqif_xhtml("")
        # Should produce valid xhtml output (not crash)
        self.assertIn("div", result.lower())

    def test_from_reqif_xhtml_strips_ns(self):
        result = from_reqif_xhtml('<xhtml:div xmlns:xhtml="http://www.w3.org/1999/xhtml">Hello</xhtml:div>')
        self.assertIn("Hello", result)
        self.assertNotIn("xhtml:", result)

    def test_from_reqif_xhtml_empty(self):
        self.assertEqual(from_reqif_xhtml(""), "")
        self.assertEqual(from_reqif_xhtml(None), "")


class TestImport(unittest.TestCase):
    def test_import_creates_spec_and_objects(self):
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()

        spec_id = import_reqif(bundle, conn, spec_slug="test-srs")

        self.assertEqual(spec_id, "test-srs")

        # Specification row
        row = conn.execute(
            "SELECT identifier, long_name FROM specifications WHERE identifier = ?",
            (spec_id,),
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "Test SRS")

        # Objects
        objects = conn.execute(
            "SELECT pid, title_text, type_ref FROM spec_objects "
            "WHERE specification_ref = ? ORDER BY file_seq",
            (spec_id,),
        ).fetchall()
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0][0], "HLR-001")
        self.assertEqual(objects[0][1], "First Requirement")
        self.assertEqual(objects[1][0], "HLR-002")

        conn.close()

    def test_import_creates_types(self):
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        import_reqif(bundle, conn, spec_slug="test")

        # Object type
        row = conn.execute(
            "SELECT identifier FROM spec_object_types WHERE identifier = 'HLR'"
        ).fetchone()
        self.assertIsNotNone(row)

        # Datatype
        row = conn.execute(
            "SELECT type FROM datatype_definitions WHERE identifier = 'STATUS'"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "ENUM")

        # Enum values
        evs = conn.execute(
            "SELECT key FROM enum_values WHERE datatype_ref = 'STATUS' ORDER BY sequence"
        ).fetchall()
        self.assertEqual([r[0] for r in evs], ["draft", "approved"])

        conn.close()

    def test_import_creates_relations(self):
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        spec_id = import_reqif(bundle, conn, spec_slug="test")

        rels = conn.execute(
            "SELECT source_object_id, target_object_id, type_ref "
            "FROM spec_relations WHERE specification_ref = ?",
            (spec_id,),
        ).fetchall()
        self.assertEqual(len(rels), 1)
        self.assertIsNotNone(rels[0][0])
        self.assertIsNotNone(rels[0][1])
        self.assertEqual(rels[0][2], "TRACES_TO")

        conn.close()

    def test_import_creates_attribute_values(self):
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        spec_id = import_reqif(bundle, conn, spec_slug="test")

        # Find the first object
        obj = conn.execute(
            "SELECT id FROM spec_objects WHERE specification_ref = ? AND pid = 'HLR-001'",
            (spec_id,),
        ).fetchone()
        self.assertIsNotNone(obj)

        # Check status attribute
        av = conn.execute(
            "SELECT name, datatype, enum_ref FROM spec_attribute_values "
            "WHERE owner_object_id = ? AND name = 'status'",
            (obj[0],),
        ).fetchone()
        self.assertIsNotNone(av)
        self.assertEqual(av[1], "ENUM")
        # enum_ref should point to the draft enum value
        self.assertIsNotNone(av[2])

        conn.close()

    def test_import_records_id_mappings(self):
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        import_reqif(bundle, conn, spec_slug="test")

        m = IdMap(conn)
        # The specification should be mapped
        result = m.get_specir_id("SPEC-1")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "specifications")

        conn.close()


class TestExport(unittest.TestCase):
    def _make_populated_db(self) -> sqlite3.Connection:
        """Create a SpecIR db with minimal content for export."""
        conn = _make_in_memory_db()
        ensure_schema(conn)

        conn.execute(
            "INSERT INTO datatype_definitions (identifier, long_name, type) "
            "VALUES ('STRING', 'String', 'STRING')"
        )
        conn.execute(
            "INSERT INTO datatype_definitions (identifier, long_name, type) "
            "VALUES ('XHTML', 'XHTML', 'XHTML')"
        )
        conn.execute(
            "INSERT INTO spec_object_types "
            "(identifier, long_name, is_default) VALUES ('SECTION', 'Section', 1)"
        )
        conn.execute(
            "INSERT INTO specifications "
            "(identifier, root_path, long_name) VALUES ('test', '/test.md', 'Test Doc')"
        )
        conn.execute(
            "INSERT INTO spec_objects "
            "(id, specification_ref, type_ref, from_file, file_seq, pid, title_text, level) "
            "VALUES (1, 'test', 'SECTION', '/test.md', 0, 'SEC-001', 'Introduction', 2)"
        )
        conn.execute(
            "INSERT INTO spec_objects "
            "(id, specification_ref, type_ref, from_file, file_seq, pid, title_text, level) "
            "VALUES (2, 'test', 'SECTION', '/test.md', 1, 'SEC-002', 'Details', 2)"
        )
        conn.commit()
        return conn

    def test_export_produces_bundle(self):
        conn = self._make_populated_db()
        bundle = export_reqif(conn, "test")
        self.assertIsInstance(bundle, ReqIFBundle)
        self.assertIsNotNone(bundle.core_content)

        content = bundle.core_content.req_if_content
        self.assertEqual(len(content.spec_objects), 2)
        self.assertEqual(len(content.specifications), 1)
        self.assertEqual(content.specifications[0].long_name, "Test Doc")

        conn.close()

    def test_export_objects_have_core_attributes(self):
        conn = self._make_populated_db()
        bundle = export_reqif(conn, "test")
        content = bundle.core_content.req_if_content

        obj = content.spec_objects[0]
        attr_names = set()
        for spec_type in content.spec_types:
            if isinstance(spec_type, ReqIFSpecObjectType):
                if spec_type.identifier == obj.spec_object_type:
                    for ad in spec_type.attribute_definitions:
                        attr_names.add(ad.long_name)

        self.assertIn("ReqIF.ForeignID", attr_names)
        self.assertIn("ReqIF.Name", attr_names)
        self.assertIn("ReqIF.Text", attr_names)

        conn.close()


class TestRoundTrip(unittest.TestCase):
    def test_import_then_export_preserves_ids(self):
        """Import a bundle, then export — ReqIF IDs should match originals."""
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        spec_id = import_reqif(bundle, conn, spec_slug="rt-test")

        # Now export
        exported = export_reqif(conn, spec_id)
        content = exported.core_content.req_if_content

        # The exported spec objects should reuse the original ReqIF identifiers
        exported_obj_ids = {obj.identifier for obj in content.spec_objects}
        self.assertIn("SO-1", exported_obj_ids)
        self.assertIn("SO-2", exported_obj_ids)

        # Relations should also reuse original IDs
        if content.spec_relations:
            exported_rel_ids = {r.identifier for r in content.spec_relations}
            self.assertIn("SR-1", exported_rel_ids)

        conn.close()

    def test_import_then_export_preserves_data(self):
        """Import → export round-trip preserves object titles and structure."""
        conn = _make_in_memory_db()
        bundle = _make_sample_bundle()
        spec_id = import_reqif(bundle, conn, spec_slug="rt-test")

        exported = export_reqif(conn, spec_id)
        content = exported.core_content.req_if_content

        # Should have same number of objects
        self.assertEqual(len(content.spec_objects), 2)

        # Titles preserved
        titles = sorted(obj.long_name for obj in content.spec_objects)
        self.assertEqual(titles, ["First Requirement", "Second Requirement"])

        # Should have the specification
        self.assertEqual(len(content.specifications), 1)

        conn.close()


if __name__ == "__main__":
    unittest.main()
