"""Import a ReqIFBundle into SpecIR (SQLite).

Pipeline stages:
  1. Bootstrap type system  — data types, object types, relation types, attribute types
  2. Populate content       — specifications, objects, hierarchy, attributes, relations
  3. Finalize               — auto-generate PIDs and labels
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from reqif.models.reqif_data_type import (
    ReqIFDataTypeDefinitionBoolean,
    ReqIFDataTypeDefinitionDateIdentifier,
    ReqIFDataTypeDefinitionEnumeration,
    ReqIFDataTypeDefinitionInteger,
    ReqIFDataTypeDefinitionReal,
    ReqIFDataTypeDefinitionString,
    ReqIFDataTypeDefinitionXHTML,
)
from reqif.models.reqif_spec_object import ReqIFSpecObject
from reqif.models.reqif_spec_object_type import ReqIFSpecObjectType
from reqif.models.reqif_spec_relation import ReqIFSpecRelation
from reqif.models.reqif_spec_relation_type import ReqIFSpecRelationType
from reqif.models.reqif_specification import ReqIFSpecification
from reqif.models.reqif_specification_type import ReqIFSpecificationType
from reqif.models.reqif_types import SpecObjectAttributeType
from reqif.reqif_bundle import ReqIFBundle

from .id_map import IdMap
from .schema import ensure_schema
from .xhtml import from_reqif_xhtml

# Source file sentinel for imported objects (no real source file).
_FROM_FILE = "<reqif-import>"


# ── helpers ──────────────────────────────────────────────────────────────

def _reqif_datatype_to_primitive(dt: Any) -> str:
    """Map a ReqIF data type object to a SpecIR primitive string."""
    if isinstance(dt, ReqIFDataTypeDefinitionString):
        return "STRING"
    if isinstance(dt, ReqIFDataTypeDefinitionInteger):
        return "INTEGER"
    if isinstance(dt, ReqIFDataTypeDefinitionReal):
        return "REAL"
    if isinstance(dt, ReqIFDataTypeDefinitionBoolean):
        return "BOOLEAN"
    if isinstance(dt, ReqIFDataTypeDefinitionDateIdentifier):
        return "DATE"
    if isinstance(dt, ReqIFDataTypeDefinitionXHTML):
        return "XHTML"
    if isinstance(dt, ReqIFDataTypeDefinitionEnumeration):
        return "ENUM"
    return "STRING"


def _attr_type_to_primitive(attr_type: SpecObjectAttributeType) -> str:
    """Map a ReqIF SpecObjectAttributeType enum to SpecIR primitive."""
    _map = {
        SpecObjectAttributeType.STRING: "STRING",
        SpecObjectAttributeType.INTEGER: "INTEGER",
        SpecObjectAttributeType.REAL: "REAL",
        SpecObjectAttributeType.BOOLEAN: "BOOLEAN",
        SpecObjectAttributeType.DATE: "DATE",
        SpecObjectAttributeType.XHTML: "XHTML",
        SpecObjectAttributeType.ENUMERATION: "ENUM",
    }
    return _map.get(attr_type, "STRING")


def _slugify(text: str) -> str:
    """Convert text to a lowercase slug suitable for labels."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


# ── Stage 1: Bootstrap type system ───────────────────────────────────────

def _import_datatypes(
    conn: sqlite3.Connection,
    data_types: List[Any],
    id_map: IdMap,
) -> Dict[str, str]:
    """Insert data types and enum values.  Returns reqif_dt_id → specir_id map."""
    reqif_to_specir_dt: Dict[str, str] = {}

    for dt in data_types:
        primitive = _reqif_datatype_to_primitive(dt)
        long_name = getattr(dt, "long_name", None) or dt.identifier
        # Use long_name as the SpecIR identifier (human-friendly key).
        specir_id = long_name.upper().replace(" ", "_") if long_name else dt.identifier
        reqif_to_specir_dt[dt.identifier] = specir_id

        conn.execute(
            "INSERT OR IGNORE INTO datatype_definitions (identifier, long_name, type) "
            "VALUES (?, ?, ?)",
            (specir_id, long_name, primitive),
        )
        id_map.put("datatype_definitions", specir_id, dt.identifier)

        # Enum values
        if isinstance(dt, ReqIFDataTypeDefinitionEnumeration) and dt.values:
            for seq, ev in enumerate(dt.values):
                # Use long_name as the key (human-readable, what users write in CommonSpec).
                # Fall back to the numeric embedded key if long_name is missing.
                display_key = ev.long_name or ev.key
                ev_specir_id = f"{specir_id}_{display_key.upper().replace(' ', '_')}"
                conn.execute(
                    "INSERT OR IGNORE INTO enum_values (identifier, datatype_ref, key, sequence) "
                    "VALUES (?, ?, ?, ?)",
                    (ev_specir_id, specir_id, display_key, seq),
                )
                id_map.put("enum_values", ev_specir_id, ev.identifier)

    # Ensure core primitives always exist.
    for p in ("STRING", "INTEGER", "REAL", "BOOLEAN", "DATE", "XHTML"):
        conn.execute(
            "INSERT OR IGNORE INTO datatype_definitions (identifier, long_name, type) "
            "VALUES (?, ?, ?)",
            (p, p, p),
        )

    return reqif_to_specir_dt


def _import_spec_types(
    conn: sqlite3.Connection,
    spec_types: List[Any],
    reqif_to_specir_dt: Dict[str, str],
    id_map: IdMap,
) -> Tuple[
    Dict[str, str],  # reqif_obj_type_id → specir_type_id
    Dict[str, str],  # reqif_rel_type_id → specir_type_id
    Dict[str, str],  # reqif_spec_type_id → specir_type_id
    Dict[str, str],  # reqif_attr_def_id → specir_attr_name (for attribute value mapping)
    Dict[str, str],  # reqif_attr_def_id → specir_datatype_primitive
]:
    obj_type_map: Dict[str, str] = {}
    rel_type_map: Dict[str, str] = {}
    spec_type_map: Dict[str, str] = {}
    attr_def_name_map: Dict[str, str] = {}
    attr_def_prim_map: Dict[str, str] = {}

    for st in spec_types:
        if isinstance(st, ReqIFSpecObjectType):
            long_name = st.long_name or st.identifier
            specir_id = long_name.upper().replace(" ", "_")
            obj_type_map[st.identifier] = specir_id

            conn.execute(
                "INSERT OR IGNORE INTO spec_object_types "
                "(identifier, long_name, description, is_default) VALUES (?, ?, ?, ?)",
                (specir_id, long_name, st.description, 0),
            )
            id_map.put("spec_object_types", specir_id, st.identifier)

            # Attribute definitions for this object type.
            if st.attribute_definitions:
                for ad in st.attribute_definitions:
                    attr_name = ad.long_name or ad.identifier
                    # Skip the 3 core ReqIF pseudo-attributes — they map to
                    # dedicated columns (pid, title_text, content_xhtml).
                    if attr_name in ("ReqIF.ForeignID", "ReqIF.Name", "ReqIF.Text"):
                        attr_def_name_map[ad.identifier] = attr_name
                        attr_def_prim_map[ad.identifier] = _attr_type_to_primitive(ad.attribute_type)
                        continue

                    dt_specir = reqif_to_specir_dt.get(ad.datatype_definition, "STRING")
                    primitive = _attr_type_to_primitive(ad.attribute_type)
                    attr_specir_id = f"{specir_id}_{attr_name}"

                    conn.execute(
                        "INSERT OR IGNORE INTO spec_attribute_types "
                        "(identifier, owner_type_ref, long_name, datatype_ref) "
                        "VALUES (?, ?, ?, ?)",
                        (attr_specir_id, specir_id, attr_name, dt_specir),
                    )
                    attr_def_name_map[ad.identifier] = attr_name
                    attr_def_prim_map[ad.identifier] = primitive

        elif isinstance(st, ReqIFSpecRelationType):
            long_name = st.long_name or st.identifier
            specir_id = long_name.upper().replace(" ", "_")
            rel_type_map[st.identifier] = specir_id

            conn.execute(
                "INSERT OR IGNORE INTO spec_relation_types "
                "(identifier, long_name, description) VALUES (?, ?, ?)",
                (specir_id, long_name, st.description),
            )
            id_map.put("spec_relation_types", specir_id, st.identifier)

        elif isinstance(st, ReqIFSpecificationType):
            long_name = st.long_name or st.identifier
            specir_id = long_name.upper().replace(" ", "_")
            spec_type_map[st.identifier] = specir_id

            conn.execute(
                "INSERT OR IGNORE INTO spec_specification_types "
                "(identifier, long_name, description) VALUES (?, ?, ?)",
                (specir_id, long_name, st.description),
            )
            id_map.put("spec_specification_types", specir_id, st.identifier)

    # Ensure a default SECTION type always exists.
    conn.execute(
        "INSERT OR IGNORE INTO spec_object_types "
        "(identifier, long_name, is_composite, is_default) VALUES (?, ?, ?, ?)",
        ("SECTION", "Section", 1, 1),
    )

    return obj_type_map, rel_type_map, spec_type_map, attr_def_name_map, attr_def_prim_map


# ── Stage 2: Populate content ────────────────────────────────────────────

def _import_specifications(
    conn: sqlite3.Connection,
    specifications: List[ReqIFSpecification],
    spec_type_map: Dict[str, str],
    id_map: IdMap,
    spec_slug: Optional[str],
) -> Dict[str, str]:
    """Insert specification rows.  Returns reqif_spec_id → specir_spec_id."""
    spec_map: Dict[str, str] = {}

    for i, spec in enumerate(specifications):
        specir_id = spec_slug or _slugify(spec.long_name or spec.identifier) or f"spec_{i}"
        type_ref = spec_type_map.get(spec.specification_type or "") if spec.specification_type else None

        conn.execute(
            "INSERT OR REPLACE INTO specifications "
            "(identifier, root_path, long_name, type_ref, pid) "
            "VALUES (?, ?, ?, ?, ?)",
            (specir_id, _FROM_FILE, spec.long_name, type_ref, None),
        )
        id_map.put("specifications", specir_id, spec.identifier)
        spec_map[spec.identifier] = specir_id

    return spec_map


def _walk_hierarchy_dfs(
    children, depth: int, seq_counter: List[int],
) -> List[Tuple[str, int, int]]:
    """DFS walk of spec hierarchy.  Returns list of (spec_object_ref, level, file_seq)."""
    result: List[Tuple[str, int, int]] = []
    if not children:
        return result
    for child in children:
        level = depth + 1  # H2 = level 2 (depth 1 + 1)
        file_seq = seq_counter[0]
        seq_counter[0] += 1
        result.append((child.spec_object, level, file_seq))
        if child.children:
            result.extend(_walk_hierarchy_dfs(child.children, depth + 1, seq_counter))
    return result


def _extract_core_attrs(
    obj: ReqIFSpecObject,
    attr_def_name_map: Dict[str, str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract ReqIF.ForeignID, ReqIF.Name, ReqIF.Text from a spec object."""
    pid = None
    title = None
    xhtml_text = None

    for attr in obj.attributes:
        name = attr_def_name_map.get(attr.definition_ref)
        if name == "ReqIF.ForeignID":
            pid = str(attr.value) if attr.value else None
        elif name == "ReqIF.Name":
            title = _normalize_string(str(attr.value)) if attr.value else None
        elif name == "ReqIF.Text":
            if attr.value:
                xhtml_text = _normalize_string(from_reqif_xhtml(str(attr.value)))
    return pid, title, xhtml_text


def _import_objects_and_hierarchy(
    conn: sqlite3.Connection,
    bundle: ReqIFBundle,
    specifications: List[ReqIFSpecification],
    spec_map: Dict[str, str],
    obj_type_map: Dict[str, str],
    attr_def_name_map: Dict[str, str],
    attr_def_prim_map: Dict[str, str],
    id_map: IdMap,
) -> Dict[str, int]:
    """Insert spec_objects and attribute values.  Returns reqif_obj_id → specir_obj_id."""
    obj_id_map: Dict[str, int] = {}

    # Build a lookup: reqif_obj_id → ReqIFSpecObject
    obj_lookup: Dict[str, ReqIFSpecObject] = {}
    content = bundle.core_content.req_if_content
    if content.spec_objects:
        for obj in content.spec_objects:
            obj_lookup[obj.identifier] = obj

    # Build reverse map: reqif enum value id → specir enum value id
    enum_rev: Dict[str, str] = {}
    for row in conn.execute("SELECT identifier FROM enum_values").fetchall():
        rid = id_map.get_reqif_id("enum_values", row[0])
        if rid:
            enum_rev[rid] = row[0]

    for spec in specifications:
        specir_spec_id = spec_map.get(spec.identifier)
        if not specir_spec_id:
            continue

        # Walk hierarchy to determine ordering and levels.
        hier_entries = _walk_hierarchy_dfs(spec.children, 1, [0])

        for reqif_obj_ref, level, file_seq in hier_entries:
            obj = obj_lookup.get(reqif_obj_ref)
            if obj is None:
                continue

            # Resolve type
            specir_type = obj_type_map.get(obj.spec_object_type, "SECTION")

            # Extract core attributes
            pid, title, content_xhtml = _extract_core_attrs(obj, attr_def_name_map)
            title = title or obj.long_name or pid or obj.identifier

            cursor = conn.execute(
                "INSERT INTO spec_objects "
                "(specification_ref, type_ref, from_file, file_seq, pid, title_text, "
                " level, content_xhtml) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (specir_spec_id, specir_type, _FROM_FILE, file_seq, pid, title, level, content_xhtml),
            )
            specir_obj_id = cursor.lastrowid
            obj_id_map[obj.identifier] = specir_obj_id
            id_map.put("spec_objects", str(specir_obj_id), obj.identifier)

            # Custom attributes (non-core)
            for attr in obj.attributes:
                attr_name = attr_def_name_map.get(attr.definition_ref)
                if not attr_name or attr_name in ("ReqIF.ForeignID", "ReqIF.Name", "ReqIF.Text"):
                    continue

                primitive = attr_def_prim_map.get(attr.definition_ref, "STRING")
                _insert_attribute_value(
                    conn, specir_spec_id, specir_obj_id, attr_name,
                    attr.value, primitive, attr.attribute_type, enum_rev,
                )

    return obj_id_map


def _normalize_string(s: str) -> str:
    """Normalise literal backslash-n sequences to real newlines.

    Some ReqIF producers (e.g. StrictDoc) encode line breaks as the two-char
    sequence ``\\n`` inside XML attribute values.  We convert these to real
    ``\\x0a`` so downstream consumers see actual paragraphs.
    """
    return s.replace("\\n", "\n")


def _insert_attribute_value(
    conn: sqlite3.Connection,
    spec_id: str,
    owner_obj_id: int,
    name: str,
    value: Any,
    primitive: str,
    attr_type: SpecObjectAttributeType,
    enum_rev: Dict[str, str],
) -> None:
    """Insert a single attribute value into the EAV table."""
    if value is None:
        return

    raw = str(value) if not isinstance(value, list) else ",".join(value)
    raw = _normalize_string(raw)

    params: Dict[str, Any] = {
        "specification_ref": spec_id,
        "owner_object_id": owner_obj_id,
        "name": name,
        "raw_value": raw,
        "datatype": primitive,
    }

    if primitive == "ENUM" and attr_type == SpecObjectAttributeType.ENUMERATION:
        # value is a list of reqif enum value identifiers
        if isinstance(value, list) and value:
            specir_enum = enum_rev.get(value[0])
            if specir_enum:
                params["enum_ref"] = specir_enum
    elif primitive == "XHTML":
        html = from_reqif_xhtml(str(value)) if value else None
        if html:
            html = _normalize_string(html)
        params["xhtml_value"] = html
        params["string_value"] = html
    elif primitive == "INTEGER":
        try:
            params["int_value"] = int(value)
        except (ValueError, TypeError):
            params["string_value"] = _normalize_string(str(value))
    elif primitive == "REAL":
        try:
            params["real_value"] = float(value)
        except (ValueError, TypeError):
            params["string_value"] = _normalize_string(str(value))
    elif primitive == "BOOLEAN":
        params["bool_value"] = 1 if str(value).lower() in ("true", "1") else 0
    elif primitive == "DATE":
        params["date_value"] = str(value)
    else:
        params["string_value"] = _normalize_string(str(value))

    cols = ", ".join(params.keys())
    placeholders = ", ".join(["?"] * len(params))
    conn.execute(
        f"INSERT INTO spec_attribute_values ({cols}) VALUES ({placeholders})",
        tuple(params.values()),
    )


def _import_relations(
    conn: sqlite3.Connection,
    relations: List[ReqIFSpecRelation],
    obj_id_map: Dict[str, int],
    rel_type_map: Dict[str, str],
    spec_id: str,
    id_map: IdMap,
) -> None:
    """Insert spec_relations from ReqIF relations."""
    for rel in relations:
        source_specir = obj_id_map.get(rel.source)
        target_specir = obj_id_map.get(rel.target)
        if source_specir is None or target_specir is None:
            continue

        type_ref = rel_type_map.get(rel.relation_type_ref)

        cursor = conn.execute(
            "INSERT INTO spec_relations "
            "(specification_ref, source_object_id, target_text, target_object_id, "
            " type_ref, from_file, link_selector) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (spec_id, source_specir, rel.target, target_specir, type_ref, _FROM_FILE, "@"),
        )
        id_map.put("spec_relations", str(cursor.lastrowid), rel.identifier)


# ── Stage 3: Finalize ────────────────────────────────────────────────────

def _finalize_pids_and_labels(conn: sqlite3.Connection, spec_id: str) -> None:
    """Auto-generate PIDs and labels for imported objects that lack them."""
    rows = conn.execute(
        "SELECT id, type_ref, pid, title_text FROM spec_objects "
        "WHERE specification_ref = ? ORDER BY type_ref, file_seq",
        (spec_id,),
    ).fetchall()

    # Count by type for auto PID generation.
    type_counters: Dict[str, int] = {}
    # Track seen labels to avoid UNIQUE constraint violations.
    seen_labels: set = set()

    for row in rows:
        obj_id, type_ref, pid, title_text = row[0], row[1], row[2], row[3]

        # Generate label: {type_lower}:{title_slug}
        label = None
        if title_text:
            base = f"{type_ref.lower()}:{_slugify(title_text)}"
            label = base
            suffix = 2
            while label in seen_labels:
                label = f"{base}-{suffix}"
                suffix += 1
            seen_labels.add(label)

        # Auto-generate PID if missing
        pid_auto = 0
        pid_prefix = None
        pid_sequence = None
        if pid:
            # Parse existing PID
            match = re.match(r"^([A-Za-z]+)-(\d+)$", pid)
            if match:
                pid_prefix = match.group(1).upper()
                pid_sequence = int(match.group(2))
        else:
            type_counters.setdefault(type_ref, 0)
            type_counters[type_ref] += 1
            pid_prefix = type_ref
            pid_sequence = type_counters[type_ref]
            pid = f"{pid_prefix}-{pid_sequence:03d}"
            pid_auto = 1

        conn.execute(
            "UPDATE spec_objects SET pid = ?, pid_prefix = ?, pid_sequence = ?, "
            "pid_auto_generated = ?, label = ? WHERE id = ?",
            (pid, pid_prefix, pid_sequence, pid_auto, label, obj_id),
        )


# ── Public API ───────────────────────────────────────────────────────────

def import_reqif(
    bundle: ReqIFBundle,
    conn: sqlite3.Connection,
    spec_slug: Optional[str] = None,
) -> str:
    """Import a ReqIFBundle into SpecIR tables.

    Parameters
    ----------
    bundle : ReqIFBundle
        Parsed ReqIF content (from ``ReqIFParser.parse``).
    conn : sqlite3.Connection
        Open SQLite connection.  Schema is created if needed.
    spec_slug : str, optional
        Override the specification identifier.  When *None*, derived from
        the first specification's ``long_name``.

    Returns
    -------
    str
        The specification identifier stored in SpecIR.
    """
    ensure_schema(conn)
    id_map = IdMap(conn)

    content = bundle.core_content.req_if_content

    # Stage 1 — type system
    reqif_to_specir_dt = _import_datatypes(
        conn, content.data_types or [], id_map,
    )
    (
        obj_type_map,
        rel_type_map,
        spec_type_map,
        attr_def_name_map,
        attr_def_prim_map,
    ) = _import_spec_types(
        conn, content.spec_types or [], reqif_to_specir_dt, id_map,
    )

    # Stage 2 — content
    specifications = content.specifications or []
    spec_map = _import_specifications(
        conn, specifications, spec_type_map, id_map, spec_slug,
    )

    obj_id_map = _import_objects_and_hierarchy(
        conn, bundle, specifications, spec_map,
        obj_type_map, attr_def_name_map, attr_def_prim_map, id_map,
    )

    # Use the first specification identifier for relations and finalization.
    specir_spec_id = next(iter(spec_map.values())) if spec_map else "imported"

    _import_relations(
        conn, content.spec_relations or [], obj_id_map, rel_type_map,
        specir_spec_id, id_map,
    )

    # Stage 3 — finalize
    _finalize_pids_and_labels(conn, specir_spec_id)

    conn.commit()
    return specir_spec_id
