"""Export a SpecIR specification to a ReqIFBundle.

Refactored from ``models/default/scripts/reqif_export.py``.  Key difference:
uses ``IdMap`` for stable/round-trip ID generation instead of raw SHA1 hashes.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from html import escape as _xml_escape
from typing import Any, Dict, List, Optional, Tuple

from reqif.models.reqif_core_content import ReqIFCoreContent
from reqif.models.reqif_data_type import (
    ReqIFDataTypeDefinitionBoolean,
    ReqIFDataTypeDefinitionDateIdentifier,
    ReqIFDataTypeDefinitionEnumeration,
    ReqIFDataTypeDefinitionInteger,
    ReqIFDataTypeDefinitionReal,
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

from .content_converter import attr_xhtml_to_html, body_to_html
from .id_map import IdMap
from .xhtml import to_reqif_xhtml


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")


# ── SQL helpers ──────────────────────────────────────────────────────────

def _get_spec_title(conn: sqlite3.Connection, spec_id: str) -> str:
    row = conn.execute(
        "SELECT long_name, pid FROM specifications WHERE identifier = ?",
        (spec_id,),
    ).fetchone()
    if not row:
        return spec_id
    return str(row[0] or row[1] or spec_id)


def _load_datatype_definitions(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute("SELECT identifier, type FROM datatype_definitions").fetchall()
    return {str(r[0]): str(r[1]) for r in rows}


def _load_enum_values(conn: sqlite3.Connection) -> Dict[str, List[Tuple[str, str]]]:
    rows = conn.execute(
        "SELECT datatype_ref, identifier, key FROM enum_values ORDER BY datatype_ref, sequence"
    ).fetchall()
    out: Dict[str, List[Tuple[str, str]]] = {}
    for r in rows:
        out.setdefault(str(r[0]), []).append((str(r[1]), str(r[2])))
    return out


def _load_object_types(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    rows = conn.execute(
        "SELECT identifier, long_name, description FROM spec_object_types ORDER BY identifier"
    ).fetchall()
    return {
        str(r[0]): {"id": str(r[0]), "long_name": str(r[1]) if r[1] else str(r[0]), "description": r[2]}
        for r in rows
    }


def _load_attribute_types(conn: sqlite3.Connection) -> list:
    return conn.execute(
        "SELECT owner_type_ref, long_name, datatype_ref "
        "FROM spec_attribute_types ORDER BY owner_type_ref, long_name"
    ).fetchall()


def _load_spec_objects(conn: sqlite3.Connection, spec_id: str) -> list:
    return conn.execute(
        "SELECT id, type_ref, pid, title_text, level, file_seq, content_xhtml, ast "
        "FROM spec_objects WHERE specification_ref = ? ORDER BY file_seq ASC",
        (spec_id,),
    ).fetchall()


def _load_attribute_values(conn: sqlite3.Connection, spec_id: str) -> Dict[str, list]:
    rows = conn.execute(
        """
        SELECT
          av.owner_object_id, av.name, av.raw_value,
          av.string_value, av.int_value, av.real_value,
          av.bool_value, av.date_value, av.enum_ref,
          av.datatype, av.xhtml_value,
          ev.key AS enum_key,
          av.ast
        FROM spec_attribute_values av
        LEFT JOIN enum_values ev ON ev.identifier = av.enum_ref
        WHERE av.specification_ref = ?
        ORDER BY av.owner_object_id, av.name
        """,
        (spec_id,),
    ).fetchall()
    out: Dict[str, list] = {}
    for r in rows:
        out.setdefault(str(r[0]), []).append(r)
    return out


def _load_relations(conn: sqlite3.Connection, spec_id: str) -> list:
    return conn.execute(
        """
        SELECT r.id, r.type_ref, r.source_object_id, r.target_object_id
        FROM spec_relations r
        JOIN spec_objects s1 ON s1.id = r.source_object_id
        JOIN spec_objects s2 ON s2.id = r.target_object_id
        WHERE r.specification_ref = ?
          AND r.target_object_id IS NOT NULL
        ORDER BY r.id
        """,
        (spec_id,),
    ).fetchall()


def _load_relation_types(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    rows = conn.execute(
        "SELECT identifier, long_name, description FROM spec_relation_types ORDER BY identifier"
    ).fetchall()
    return {
        str(r[0]): {"id": str(r[0]), "long_name": str(r[1]) if r[1] else str(r[0]), "description": r[2]}
        for r in rows
    }


# ── Hierarchy builder ────────────────────────────────────────────────────

def _build_hierarchy(objects: list) -> List[Tuple[Any, list]]:
    """Build tree from flat ordered objects using level."""
    root: List[Tuple[Any, list]] = []
    stack: List[Tuple[int, list]] = [(0, root)]

    for row in objects:
        hier_level = max(1, int(row[4] or 2) - 1)
        while stack and hier_level <= stack[-1][0]:
            stack.pop()
        parent_children = stack[-1][1] if stack else root
        node: Tuple[Any, list] = (row, [])
        parent_children.append(node)
        stack.append((hier_level, node[1]))
    return root


# ── Public API ───────────────────────────────────────────────────────────

def export_reqif(conn: sqlite3.Connection, spec_id: str) -> ReqIFBundle:
    """Export a specification from SpecIR to a ReqIFBundle.

    Parameters
    ----------
    conn : sqlite3.Connection
        Open SQLite connection to a SpecIR database.
    spec_id : str
        The specification identifier to export.

    Returns
    -------
    ReqIFBundle
        Ready for serialization via ``ReqIFUnparser.unparse()``.
    """
    id_map = IdMap(conn)
    now = _now()
    spec_title = _get_spec_title(conn, spec_id)

    # ── data types ──
    datatype_types = _load_datatype_definitions(conn)
    enum_values_by_dt = _load_enum_values(conn)

    reqif_datatypes: Dict[str, Any] = {}
    for dt_id, primitive in sorted(datatype_types.items()):
        reqif_id = id_map.ensure_reqif_id("datatype_definitions", dt_id, "DT")
        reqif_datatypes[dt_id] = _make_datatype(
            reqif_id, dt_id, primitive, now, enum_values_by_dt, id_map,
        )

    # Ensure core datatypes.
    for core in ("STRING", "XHTML"):
        if core not in reqif_datatypes:
            reqif_id = id_map.ensure_reqif_id("datatype_definitions", core, "DT")
            reqif_datatypes[core] = _make_datatype(
                reqif_id, core, core, now, enum_values_by_dt, id_map,
            )

    # ── core attribute definitions (ForeignID, Name, Text) ──
    core_defs = _make_core_attribute_defs(reqif_datatypes, id_map)

    # ── object types + per-type attribute defs ──
    object_types = _load_object_types(conn)
    attribute_types_rows = _load_attribute_types(conn)
    attr_values_by_owner = _load_attribute_values(conn, spec_id)

    reqif_attr_defs_by_owner, reqif_spec_object_types = _build_object_types(
        object_types, attribute_types_rows, datatype_types,
        reqif_datatypes, core_defs, id_map, now,
    )

    # ── spec objects + hierarchy ──
    objects = _load_spec_objects(conn, spec_id)
    (
        reqif_objects,
        reqif_object_id_by_sd_id,
    ) = _build_spec_objects(
        objects, reqif_spec_object_types, core_defs,
        reqif_attr_defs_by_owner, attr_values_by_owner,
        enum_values_by_dt, datatype_types, id_map, now,
    )

    hierarchy_tree = _build_hierarchy(objects)

    def make_hierarchy_nodes(nodes):
        out = []
        for row, children in nodes:
            sd_level = row[4] or 2
            hier_level = max(1, int(sd_level) - 1)
            sd_id = str(row[0])
            out.append(
                ReqIFSpecHierarchy(
                    xml_node=None,
                    is_self_closed=False,
                    identifier=id_map.ensure_reqif_id(
                        "spec_hierarchy", f"{spec_id}:{sd_id}", "H",
                    ),
                    last_change=now,
                    long_name=None,
                    spec_object=reqif_object_id_by_sd_id[sd_id],
                    children=make_hierarchy_nodes(children),
                    ref_then_children_order=True,
                    level=hier_level,
                )
            )
        return out

    spec_type = ReqIFSpecificationType(
        identifier=id_map.ensure_reqif_id(
            "spec_specification_types", "SpecCompiler.SpecificationType", "ST",
        ),
        last_change=now,
        long_name="SpecCompiler Specification",
        spec_attributes=None,
        spec_attribute_map={},
        is_self_closed=True,
    )

    specification = ReqIFSpecification(
        identifier=id_map.ensure_reqif_id("specifications", spec_id, "S"),
        last_change=now,
        long_name=spec_title,
        values=[],
        specification_type=spec_type.identifier,
        children=make_hierarchy_nodes(hierarchy_tree),
    )

    # ── relation types + relations ──
    relation_types = _load_relation_types(conn)
    reqif_relation_types: Dict[str, ReqIFSpecRelationType] = {}
    for rel_id, rel in relation_types.items():
        reqif_relation_types[rel_id] = ReqIFSpecRelationType(
            identifier=id_map.ensure_reqif_id("spec_relation_types", rel_id, "SRT"),
            description=rel.get("description"),
            last_change=now,
            long_name=rel.get("long_name") or rel_id,
            is_self_closed=True,
            attribute_definitions=None,
        )

    default_rel = sorted(relation_types.keys())[0] if relation_types else None
    reqif_relations = _build_relations(
        conn, spec_id, reqif_relation_types, reqif_object_id_by_sd_id,
        default_rel, id_map, now,
    )

    # ── assemble bundle ──
    reqif_content = ReqIFReqIFContent(
        data_types=list(reqif_datatypes.values()),
        spec_types=[
            spec_type,
            *reqif_spec_object_types.values(),
            *reqif_relation_types.values(),
        ],
        spec_objects=reqif_objects,
        spec_relations=reqif_relations,
        specifications=[specification],
        spec_relation_groups=[],
    )

    return ReqIFBundle(
        namespace_info=ReqIFNamespaceInfo.create_default(),
        req_if_header=ReqIFReqIFHeader(
            identifier=id_map.ensure_reqif_id("reqif_header", spec_id, "HDR"),
            creation_time=now,
            repository_id="speccompiler",
            req_if_tool_id="speccompiler",
            req_if_version="1.0",
            source_tool_id="speccompiler",
            title=f"SpecCompiler export: {spec_title}",
        ),
        core_content=ReqIFCoreContent(req_if_content=reqif_content),
        tool_extensions_tag_exists=False,
        lookup=ReqIFObjectLookup.empty(),
        exceptions=[],
    )


# ── internal helpers ─────────────────────────────────────────────────────

def _make_datatype(
    reqif_id: str,
    dt_id: str,
    primitive: str,
    now: str,
    enum_values_by_dt: Dict[str, List[Tuple[str, str]]],
    id_map: IdMap,
) -> Any:
    if primitive == "STRING":
        return ReqIFDataTypeDefinitionString(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "INTEGER":
        return ReqIFDataTypeDefinitionInteger(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "REAL":
        return ReqIFDataTypeDefinitionReal(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "BOOLEAN":
        return ReqIFDataTypeDefinitionBoolean(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "DATE":
        return ReqIFDataTypeDefinitionDateIdentifier(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "XHTML":
        return ReqIFDataTypeDefinitionXHTML(identifier=reqif_id, long_name=dt_id, last_change=now)
    if primitive == "ENUM":
        values = []
        for enum_identifier, enum_key in enum_values_by_dt.get(dt_id, []):
            values.append(ReqIFEnumValue.create(
                identifier=id_map.ensure_reqif_id("enum_values", enum_identifier, "EV"),
                key=enum_key,
            ))
        return ReqIFDataTypeDefinitionEnumeration(identifier=reqif_id, long_name=dt_id, last_change=now, values=values)
    return ReqIFDataTypeDefinitionString(identifier=reqif_id, long_name=dt_id, last_change=now)


def _make_core_attribute_defs(
    reqif_datatypes: Dict[str, Any],
    id_map: IdMap,
) -> Dict[str, SpecAttributeDefinition]:
    return {
        "foreign_id": SpecAttributeDefinition.create(
            attribute_type=SpecObjectAttributeType.STRING,
            identifier=id_map.ensure_reqif_id("attr_def", "ReqIF.ForeignID", "AD"),
            datatype_definition=reqif_datatypes["STRING"].identifier,
            long_name="ReqIF.ForeignID",
        ),
        "name": SpecAttributeDefinition.create(
            attribute_type=SpecObjectAttributeType.STRING,
            identifier=id_map.ensure_reqif_id("attr_def", "ReqIF.Name", "AD"),
            datatype_definition=reqif_datatypes["STRING"].identifier,
            long_name="ReqIF.Name",
        ),
        "text": SpecAttributeDefinition.create(
            attribute_type=SpecObjectAttributeType.XHTML,
            identifier=id_map.ensure_reqif_id("attr_def", "ReqIF.Text", "AD"),
            datatype_definition=reqif_datatypes["XHTML"].identifier,
            long_name="ReqIF.Text",
        ),
    }


def _build_object_types(
    object_types, attribute_types_rows, datatype_types,
    reqif_datatypes, core_defs, id_map, now,
):
    reqif_attr_defs_by_owner: Dict[str, Dict[str, SpecAttributeDefinition]] = {}

    for row in attribute_types_rows:
        owner = str(row[0])
        name = str(row[1])
        datatype_ref = str(row[2])
        primitive = datatype_types.get(datatype_ref, "STRING")

        if name in ("ReqIF.ForeignID", "ReqIF.Name", "ReqIF.Text"):
            continue

        attribute_type = {
            "ENUM": SpecObjectAttributeType.ENUMERATION,
            "INTEGER": SpecObjectAttributeType.INTEGER,
            "REAL": SpecObjectAttributeType.REAL,
            "BOOLEAN": SpecObjectAttributeType.BOOLEAN,
            "DATE": SpecObjectAttributeType.DATE,
            "XHTML": SpecObjectAttributeType.XHTML,
        }.get(primitive, SpecObjectAttributeType.STRING)

        reqif_def = SpecAttributeDefinition.create(
            attribute_type=attribute_type,
            identifier=id_map.ensure_reqif_id("attr_def", f"{owner}:{name}", "AD"),
            datatype_definition=reqif_datatypes.get(datatype_ref, reqif_datatypes["STRING"]).identifier,
            long_name=name,
        )
        reqif_attr_defs_by_owner.setdefault(owner, {})[name] = reqif_def

    reqif_spec_object_types: Dict[str, ReqIFSpecObjectType] = {}
    for type_id, info in object_types.items():
        defs = [core_defs["foreign_id"], core_defs["name"], core_defs["text"]]
        defs.extend(reqif_attr_defs_by_owner.get(type_id, {}).values())
        reqif_spec_object_types[type_id] = ReqIFSpecObjectType.create(
            identifier=id_map.ensure_reqif_id("spec_object_types", type_id, "SOT"),
            long_name=info.get("long_name") or type_id,
            description=info.get("description"),
            last_change=now,
            attribute_definitions=defs,
        )

    return reqif_attr_defs_by_owner, reqif_spec_object_types


def _build_spec_objects(
    objects, reqif_spec_object_types, core_defs,
    reqif_attr_defs_by_owner, attr_values_by_owner,
    enum_values_by_dt, datatype_types, id_map, now,
):
    # Build enum lookup
    reqif_enum_id_by_sd: Dict[str, str] = {}
    for dt_id, enum_rows in enum_values_by_dt.items():
        for enum_identifier, _ in enum_rows:
            reqif_enum_id_by_sd[enum_identifier] = id_map.ensure_reqif_id(
                "enum_values", enum_identifier, "EV",
            )

    reqif_objects: List[ReqIFSpecObject] = []
    reqif_object_id_by_sd_id: Dict[str, str] = {}

    for row in objects:
        sd_id = str(row[0])
        type_ref = str(row[1])
        pid = str(row[2]) if row[2] else sd_id
        title = str(row[3]) if row[3] else pid
        content_xhtml = row[6]
        ast_json = row[7] if len(row) > 7 else None

        reqif_obj_id = id_map.ensure_reqif_id("spec_objects", sd_id, "SO")
        reqif_object_id_by_sd_id[sd_id] = reqif_obj_id

        values: List[SpecObjectAttribute] = []

        # Core attributes
        values.append(SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.STRING,
            definition_ref=core_defs["foreign_id"].identifier,
            value=str(pid),
        ))
        values.append(SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.STRING,
            definition_ref=core_defs["name"].identifier,
            value=str(title),
        ))
        # Resolve body HTML: prefer content_xhtml, fall back to ast→HTML
        body_html = body_to_html(ast_json=ast_json, content_xhtml=content_xhtml)
        xhtml_value = to_reqif_xhtml(body_html or "")
        values.append(SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.XHTML,
            definition_ref=core_defs["text"].identifier,
            value=xhtml_value,
            value_stripped_xhtml=None,
        ))

        # Custom attributes
        owner_attrs = attr_values_by_owner.get(sd_id, [])
        defs_for_type = reqif_attr_defs_by_owner.get(type_ref, {})
        for av in owner_attrs:
            name = str(av[1])
            if name in ("ReqIF.ForeignID", "ReqIF.Name", "ReqIF.Text"):
                continue
            if name not in defs_for_type:
                continue

            reqif_def = defs_for_type[name]
            primitive = str(av[9]) if av[9] else "STRING"

            attr_val = _cast_attribute_value(av, primitive, reqif_def, reqif_enum_id_by_sd)
            if attr_val is not None:
                values.append(attr_val)

        obj_type = reqif_spec_object_types.get(type_ref) or reqif_spec_object_types.get("SECTION")
        assert obj_type is not None, f"No ReqIF type for {type_ref}"

        reqif_objects.append(ReqIFSpecObject(
            identifier=reqif_obj_id,
            attributes=values,
            spec_object_type=obj_type.identifier,
            long_name=_xml_escape(title, quote=True),
            last_change=now,
        ))

    return reqif_objects, reqif_object_id_by_sd_id


def _cast_attribute_value(
    av, primitive: str, reqif_def: SpecAttributeDefinition,
    reqif_enum_id_by_sd: Dict[str, str],
) -> Optional[SpecObjectAttribute]:
    """Cast a SpecIR attribute value row into a ReqIF SpecObjectAttribute."""
    if primitive == "ENUM":
        if av[8] is None:  # enum_ref
            return None
        reqif_enum_id = reqif_enum_id_by_sd.get(str(av[8]))
        if not reqif_enum_id:
            return None
        return SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.ENUMERATION,
            definition_ref=reqif_def.identifier,
            value=[reqif_enum_id],
        )
    elif primitive == "XHTML":
        xhtml_val = (str(av[10]) if av[10] else "").strip()  # xhtml_value
        ast_val = av[12] if len(av) > 12 else None  # ast
        frag = attr_xhtml_to_html(
            ast_json=ast_val, xhtml_value=xhtml_val or None,
            string_value=(str(av[3]) if av[3] else None),
        )
        if not frag:
            return None
        return SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.XHTML,
            definition_ref=reqif_def.identifier,
            value=to_reqif_xhtml(frag),
            value_stripped_xhtml=None,
        )
    else:
        # STRING, INTEGER, REAL, BOOLEAN, DATE — all stored as string in ReqIF
        val = None
        if av[3] is not None:      # string_value
            val = str(av[3])
        elif av[4] is not None:    # int_value
            val = str(av[4])
        elif av[5] is not None:    # real_value
            val = str(av[5])
        elif av[6] is not None:    # bool_value
            val = "true" if int(av[6]) == 1 else "false"
        elif av[7] is not None:    # date_value
            val = str(av[7])
        elif av[2] is not None:    # raw_value
            val = str(av[2])
        if val is None:
            return None
        return SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.STRING,
            definition_ref=reqif_def.identifier,
            value=val,
        )


def _build_relations(
    conn, spec_id, reqif_relation_types,
    reqif_object_id_by_sd_id, default_rel, id_map, now,
):
    reqif_relations: List[ReqIFSpecRelation] = []
    for rel in _load_relations(conn, spec_id):
        type_ref = str(rel[1]) if rel[1] else default_rel
        if not type_ref or type_ref not in reqif_relation_types:
            continue
        src = str(rel[2])
        tgt = str(rel[3])
        if src not in reqif_object_id_by_sd_id or tgt not in reqif_object_id_by_sd_id:
            continue
        reqif_relations.append(ReqIFSpecRelation(
            identifier=id_map.ensure_reqif_id("spec_relations", str(rel[0]), "SR"),
            relation_type_ref=reqif_relation_types[type_ref].identifier,
            source=reqif_object_id_by_sd_id[src],
            target=reqif_object_id_by_sd_id[tgt],
            last_change=now,
            long_name=None,
        ))
    return reqif_relations
