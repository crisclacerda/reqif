"""Decompile SpecIR content tables into CommonSpec markdown files.

Reads specifications, spec_objects, spec_attribute_values, and spec_relations
to produce ``.md`` files that SpecCompiler can compile.

Body content is converted from Pandoc AST JSON or HTML to clean Markdown
using the :mod:`content_converter` module.
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

from .content_converter import attr_xhtml_to_markdown, body_to_markdown


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-") or "untitled"


# ── Data loading ──────────────────────────────────────────────────────────

def _load_specification(conn: sqlite3.Connection, spec_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT identifier, long_name, type_ref, pid FROM specifications WHERE identifier = ?",
        (spec_id,),
    ).fetchone()
    return dict(row) if row else None


def _load_objects(conn: sqlite3.Connection, spec_id: str) -> List[dict]:
    rows = conn.execute(
        "SELECT id, type_ref, pid, title_text, level, content_xhtml, ast, file_seq "
        "FROM spec_objects WHERE specification_ref = ? ORDER BY file_seq",
        (spec_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _load_attributes_by_object(conn: sqlite3.Connection, spec_id: str) -> Dict[int, List[dict]]:
    """Return {owner_object_id: [attr_dict, ...]} for all attributes in a spec."""
    rows = conn.execute(
        "SELECT owner_object_id, name, raw_value, string_value, int_value, "
        "real_value, bool_value, date_value, enum_ref, datatype, xhtml_value, ast "
        "FROM spec_attribute_values WHERE specification_ref = ? AND owner_object_id IS NOT NULL "
        "ORDER BY id",
        (spec_id,),
    ).fetchall()
    result: Dict[int, List[dict]] = {}
    for r in rows:
        d = dict(r)
        oid = d["owner_object_id"]
        result.setdefault(oid, []).append(d)
    return result


def _load_relations_by_source(conn: sqlite3.Connection, spec_id: str) -> Dict[int, List[dict]]:
    """Return {source_object_id: [rel_dict, ...]} for all relations in a spec."""
    rows = conn.execute(
        "SELECT sr.source_object_id, sr.target_text, sr.target_object_id, "
        "sr.type_ref, sr.link_selector, tgt.pid AS target_pid "
        "FROM spec_relations sr "
        "LEFT JOIN spec_objects tgt ON sr.target_object_id = tgt.id "
        "WHERE sr.specification_ref = ? "
        "ORDER BY sr.id",
        (spec_id,),
    ).fetchall()
    result: Dict[int, List[dict]] = {}
    for r in rows:
        d = dict(r)
        sid = d["source_object_id"]
        result.setdefault(sid, []).append(d)
    return result


def _load_enum_key(conn: sqlite3.Connection, enum_ref: str) -> Optional[str]:
    """Look up enum value key from its identifier."""
    row = conn.execute(
        "SELECT key FROM enum_values WHERE identifier = ?",
        (enum_ref,),
    ).fetchone()
    return row[0] if row else None


# ── Rendering helpers ─────────────────────────────────────────────────────

def _format_attr_value(conn: sqlite3.Connection, attr: dict) -> Optional[str]:
    """Format an EAV attribute value for CommonSpec ``> name: value`` syntax."""
    dt = attr["datatype"]
    if dt == "ENUM":
        if attr.get("enum_ref"):
            return _load_enum_key(conn, attr["enum_ref"])
        return attr.get("raw_value")
    elif dt == "BOOLEAN":
        return "true" if attr.get("bool_value") else "false"
    elif dt == "XHTML":
        return attr_xhtml_to_markdown(
            ast_json=attr.get("ast"),
            xhtml_value=attr.get("xhtml_value"),
            string_value=attr.get("string_value"),
        )
    elif dt == "INTEGER":
        v = attr.get("int_value")
        return str(v) if v is not None else attr.get("raw_value")
    elif dt == "REAL":
        v = attr.get("real_value")
        return str(v) if v is not None else attr.get("raw_value")
    elif dt == "DATE":
        return attr.get("date_value") or attr.get("raw_value")
    else:  # STRING
        return attr.get("string_value") or attr.get("raw_value")


def _render_specification_header(
    spec: dict, spec_attrs: List[dict], conn: sqlite3.Connection
) -> str:
    """Render the H1 specification header with attributes."""
    lines: List[str] = []
    type_prefix = f"{spec['type_ref']}: " if spec.get("type_ref") else ""
    pid_suffix = f" @{spec['pid']}" if spec.get("pid") else ""
    title = spec.get("long_name") or spec.get("identifier") or "Untitled"
    lines.append(f"# {type_prefix}{title}{pid_suffix}")
    lines.append("")

    for attr in spec_attrs:
        val = _format_attr_value(conn, attr)
        if val is not None:
            lines.append(f"> {attr['name']}: {val}")
            lines.append("")

    return "\n".join(lines)


def _render_object(
    conn: sqlite3.Connection,
    obj: dict,
    attrs: List[dict],
    relations: List[dict],
    level: int,
) -> str:
    """Render a single spec object as CommonSpec markdown."""
    lines: List[str] = []

    # Header: ## TYPE: Title @PID
    hashes = "#" * level
    type_ref = obj.get("type_ref", "")
    type_prefix = f"{type_ref}: " if type_ref and type_ref != "SECTION" else ""
    pid_suffix = f" @{obj['pid']}" if obj.get("pid") else ""
    title = obj.get("title_text") or "Untitled"
    lines.append(f"{hashes} {type_prefix}{title}{pid_suffix}")
    lines.append("")

    # Attributes (> name: value)
    for attr in attrs:
        val = _format_attr_value(conn, attr)
        if val is not None:
            lines.append(f"> {attr['name']}: {val}")
            lines.append("")

    # Body content: ast (Pandoc JSON) → content_xhtml (HTML) → nothing
    body_md = body_to_markdown(
        ast_json=obj.get("ast"),
        content_xhtml=obj.get("content_xhtml"),
    )
    if body_md:
        lines.append(body_md)
        lines.append("")

    # Relations: [TARGET-PID](@)
    for rel in relations:
        target = rel.get("target_pid") or rel.get("target_text") or ""
        if not target:
            continue
        selector = rel.get("link_selector") or "@"
        lines.append(f"[{target}]({selector})")
        lines.append("")

    return "\n".join(lines)


# ── Hierarchy + file splitting ────────────────────────────────────────────

def _build_h2_groups(objects: List[dict]) -> List[List[dict]]:
    """Group objects into H2-level sections.

    Each group starts with a level-2 object and includes all deeper descendants
    until the next level-2 object.
    """
    groups: List[List[dict]] = []
    current: List[dict] = []

    for obj in objects:
        level = obj.get("level", 2)
        if level <= 2 and current:
            groups.append(current)
            current = []
        current.append(obj)

    if current:
        groups.append(current)

    return groups


def _render_group(
    conn: sqlite3.Connection,
    group: List[dict],
    attrs_by_obj: Dict[int, List[dict]],
    rels_by_src: Dict[int, List[dict]],
) -> str:
    """Render a group of objects as markdown."""
    parts: List[str] = []
    for obj in group:
        oid = obj["id"]
        level = obj.get("level", 2)
        attrs = attrs_by_obj.get(oid, [])
        rels = rels_by_src.get(oid, [])
        parts.append(_render_object(conn, obj, attrs, rels, level))
    return "\n".join(parts)


def _write_file(path: str, content: str, overwrite: bool) -> bool:
    """Write content to file. Returns True if written, False if skipped."""
    if os.path.exists(path) and not overwrite:
        print(f"skip (exists): {path}", file=sys.stderr)
        return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


# ── Public API ────────────────────────────────────────────────────────────

def decompile(
    conn: sqlite3.Connection,
    spec_id: str,
    output_dir: str,
    *,
    children_threshold: int = 50,
    overwrite: bool = False,
) -> List[str]:
    """Decompile a SpecIR specification into CommonSpec markdown files.

    Parameters
    ----------
    conn : sqlite3.Connection
        Open connection with ``row_factory = sqlite3.Row``.
    spec_id : str
        Specification identifier in SpecIR.
    output_dir : str
        Directory where ``.md`` files are written.
    children_threshold : int
        If total objects exceed this, split into multiple files.
    overwrite : bool
        If True, overwrite existing files. Otherwise skip them.

    Returns
    -------
    list[str]
        Paths of generated files.
    """
    conn.row_factory = sqlite3.Row

    spec = _load_specification(conn, spec_id)
    if spec is None:
        raise ValueError(f"Specification not found: {spec_id}")

    objects = _load_objects(conn, spec_id)
    attrs_by_obj = _load_attributes_by_object(conn, spec_id)
    rels_by_src = _load_relations_by_source(conn, spec_id)

    # Spec-level attributes (owner_object_id IS NULL, no float owner either).
    spec_attrs_rows = conn.execute(
        "SELECT name, raw_value, string_value, int_value, real_value, "
        "bool_value, date_value, enum_ref, datatype, xhtml_value, ast "
        "FROM spec_attribute_values "
        "WHERE specification_ref = ? AND owner_object_id IS NULL AND owner_float_id IS NULL "
        "ORDER BY id",
        (spec_id,),
    ).fetchall()
    spec_attrs = [dict(r) for r in spec_attrs_rows]

    spec_slug = _slugify(spec.get("long_name") or spec_id)
    h2_groups = _build_h2_groups(objects)
    generated: List[str] = []

    # Decide single vs multi file.
    if len(objects) <= children_threshold or len(h2_groups) <= 1:
        # Single file.
        parts: List[str] = [_render_specification_header(spec, spec_attrs, conn)]
        for group in h2_groups:
            parts.append(_render_group(conn, group, attrs_by_obj, rels_by_src))
        content = "\n".join(parts)
        path = os.path.join(output_dir, f"{spec_slug}.md")
        if _write_file(path, content, overwrite):
            generated.append(path)
    else:
        # Multi-file: root with includes + one file per H2 group.
        child_dir = os.path.join(output_dir, spec_slug)
        child_filenames: List[str] = []

        for group in h2_groups:
            first = group[0]
            group_slug = _slugify(first.get("title_text") or f"section-{first['file_seq']}")
            child_filename = f"{group_slug}.md"
            # Handle duplicate filenames.
            base = group_slug
            counter = 2
            while child_filename in child_filenames:
                child_filename = f"{base}-{counter}.md"
                counter += 1
            child_filenames.append(child_filename)

            child_content = _render_group(conn, group, attrs_by_obj, rels_by_src)
            child_path = os.path.join(child_dir, child_filename)
            if _write_file(child_path, child_content, overwrite):
                generated.append(child_path)

        # Root file: spec header + include block.
        parts = [_render_specification_header(spec, spec_attrs, conn)]
        include_lines = "\n".join(f"{spec_slug}/{fn}" for fn in child_filenames)
        parts.append(f"```{{.include}}\n{include_lines}\n```\n")
        root_content = "\n".join(parts)
        root_path = os.path.join(output_dir, f"{spec_slug}.md")
        if _write_file(root_path, root_content, overwrite):
            generated.append(root_path)

    return generated
