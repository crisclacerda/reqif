"""Generate Lua model type files from SpecIR type system tables.

Reads spec_object_types, spec_relation_types, spec_specification_types,
spec_attribute_types, datatype_definitions, and enum_values to produce
Lua files matching the patterns in models/*/types/.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


# ── Lua code templates ────────────────────────────────────────────────────

_OBJECT_TYPE_TEMPLATE = """\
local M = {{}}

M.object = {{
    id = "{id}",
    long_name = "{long_name}",
    description = "{description}",{extends}{is_composite}{is_default}{pid_prefix}{pid_format}{numbered}
    attributes = {{
{attributes}    }}
}}

return M
"""

_RELATION_TYPE_TEMPLATE = """\
local M = {{}}

M.relation = {{
    id = "{id}",
    extends = "PID_REF",
    long_name = "{long_name}",
    description = "{description}",
}}

return M
"""

_SPECIFICATION_TYPE_TEMPLATE = """\
local M = {{}}

M.specification = {{
    id = "{id}",
    long_name = "{long_name}",
    description = "{description}",{extends}{is_default}
    attributes = {{
{attributes}    }}
}}

return M
"""

# Built-in types that already exist in the default model — skip generation.
_BUILTIN_OBJECT_TYPES = {"SECTION"}
_BUILTIN_RELATION_TYPES = {"PID_REF", "LABEL_REF"}
_BUILTIN_SPEC_TYPES = {"SPEC"}


def _lua_escape(s: str) -> str:
    """Escape a string for Lua string literals."""
    if s is None:
        return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_attribute(name: str, datatype: str, enum_values: List[str]) -> str:
    """Format a single attribute entry for Lua."""
    if datatype == "ENUM" and enum_values:
        vals = ", ".join(f'"{_lua_escape(v)}"' for v in enum_values)
        return f'        {{ name = "{_lua_escape(name)}", type = "ENUM", values = {{ {vals} }} }},'
    return f'        {{ name = "{_lua_escape(name)}", type = "{datatype}" }},'


def _get_enum_values(conn: sqlite3.Connection, datatype_ref: str) -> List[str]:
    """Get ordered enum value keys for a datatype."""
    rows = conn.execute(
        "SELECT key FROM enum_values WHERE datatype_ref = ? ORDER BY sequence",
        (datatype_ref,),
    ).fetchall()
    return [r[0] for r in rows]


def _get_attributes(
    conn: sqlite3.Connection, owner_type_ref: str
) -> List[Tuple[str, str, List[str]]]:
    """Get attributes for a type: list of (name, primitive, enum_values)."""
    rows = conn.execute(
        "SELECT long_name, datatype_ref FROM spec_attribute_types "
        "WHERE owner_type_ref = ? ORDER BY identifier",
        (owner_type_ref,),
    ).fetchall()

    result = []
    for name, dt_ref in rows:
        # Look up the primitive type from the datatype definition.
        dt_row = conn.execute(
            "SELECT type FROM datatype_definitions WHERE identifier = ?",
            (dt_ref,),
        ).fetchone()
        primitive = dt_row[0] if dt_row else "STRING"

        enum_vals: List[str] = []
        if primitive == "ENUM":
            enum_vals = _get_enum_values(conn, dt_ref)

        result.append((name, primitive, enum_vals))
    return result


def _generate_object_type(
    conn: sqlite3.Connection, row: sqlite3.Row, output_dir: str
) -> Optional[str]:
    """Generate a single object type Lua file. Returns path or None if skipped."""
    type_id = row["identifier"]
    if type_id in _BUILTIN_OBJECT_TYPES:
        return None

    attrs = _get_attributes(conn, type_id)
    attr_lines = "\n".join(_format_attribute(n, p, ev) for n, p, ev in attrs)
    if attr_lines:
        attr_lines += "\n"

    extends_str = ""
    if row["extends"]:
        extends_str = f'\n    extends = "{_lua_escape(row["extends"])}",'

    is_composite_str = ""
    if row["is_composite"]:
        is_composite_str = "\n    is_composite = true,"

    is_default_str = ""
    if row["is_default"]:
        is_default_str = "\n    is_default = true,"

    pid_prefix_str = ""
    if row["pid_prefix"]:
        pid_prefix_str = f'\n    pid_prefix = "{_lua_escape(row["pid_prefix"])}",'
    else:
        # Auto-generate pid_prefix: use initials of words in the type ID.
        # E.g., "TC1300_SPECOBJECTTYPE" -> "TC1300_SOT" is too long,
        # so just use the type_id itself (capped at 10 chars).
        prefix = type_id[:10].upper()
        pid_prefix_str = f'\n    pid_prefix = "{prefix}",'

    pid_format_str = ""
    if row["pid_format"] and row["pid_format"] != "%s-%03d":
        pid_format_str = f'\n    pid_format = "{_lua_escape(row["pid_format"])}",'

    numbered_str = ""

    content = _OBJECT_TYPE_TEMPLATE.format(
        id=_lua_escape(type_id),
        long_name=_lua_escape(row["long_name"]),
        description=_lua_escape(row["description"] or "Imported from ReqIF"),
        extends=extends_str,
        is_composite=is_composite_str,
        is_default=is_default_str,
        pid_prefix=pid_prefix_str,
        pid_format=pid_format_str,
        numbered=numbered_str,
        attributes=attr_lines,
    )

    path = os.path.join(output_dir, "types", "objects", f"{type_id.lower()}.lua")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _generate_relation_type(row: sqlite3.Row, output_dir: str) -> Optional[str]:
    """Generate a single relation type Lua file."""
    type_id = row["identifier"]
    if type_id in _BUILTIN_RELATION_TYPES:
        return None

    content = _RELATION_TYPE_TEMPLATE.format(
        id=_lua_escape(type_id),
        long_name=_lua_escape(row["long_name"]),
        description=_lua_escape(row["description"] or "Imported from ReqIF"),
    )

    path = os.path.join(output_dir, "types", "relations", f"{type_id.lower()}.lua")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _generate_specification_type(
    conn: sqlite3.Connection, row: sqlite3.Row, output_dir: str
) -> Optional[str]:
    """Generate a single specification type Lua file."""
    type_id = row["identifier"]
    if type_id in _BUILTIN_SPEC_TYPES:
        return None

    # Spec types don't currently have attributes in SpecIR, but future-proof.
    attrs = _get_attributes(conn, type_id)
    attr_lines = "\n".join(_format_attribute(n, p, ev) for n, p, ev in attrs)
    if attr_lines:
        attr_lines += "\n"

    extends_str = ""
    if row["extends"]:
        extends_str = f'\n    extends = "{_lua_escape(row["extends"])}",'

    is_default_str = ""
    if row["is_default"]:
        is_default_str = "\n    is_default = true,"

    content = _SPECIFICATION_TYPE_TEMPLATE.format(
        id=_lua_escape(type_id),
        long_name=_lua_escape(row["long_name"]),
        description=_lua_escape(row["description"] or "Imported from ReqIF"),
        extends=extends_str,
        is_default=is_default_str,
        attributes=attr_lines,
    )

    path = os.path.join(output_dir, "types", "specifications", f"{type_id.lower()}.lua")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_model(
    conn: sqlite3.Connection,
    output_dir: str,
    model_name: str = "imported",
) -> str:
    """Generate Lua type files from SpecIR type system.

    Creates ``{output_dir}/models/{model_name}/types/{objects,relations,specifications}/*.lua``

    Parameters
    ----------
    conn : sqlite3.Connection
        Open connection with row_factory = sqlite3.Row.
    output_dir : str
        Root project directory.
    model_name : str
        Model subdirectory name (default: ``"imported"``).

    Returns
    -------
    str
        Path to the model directory.
    """
    conn.row_factory = sqlite3.Row
    model_dir = os.path.join(output_dir, "models", model_name)
    generated: List[str] = []

    # Object types
    rows = conn.execute(
        "SELECT * FROM spec_object_types ORDER BY identifier"
    ).fetchall()
    for row in rows:
        path = _generate_object_type(conn, row, model_dir)
        if path:
            generated.append(path)

    # Relation types
    rows = conn.execute(
        "SELECT * FROM spec_relation_types ORDER BY identifier"
    ).fetchall()
    for row in rows:
        path = _generate_relation_type(row, model_dir)
        if path:
            generated.append(path)

    # Specification types
    rows = conn.execute(
        "SELECT * FROM spec_specification_types ORDER BY identifier"
    ).fetchall()
    for row in rows:
        path = _generate_specification_type(conn, row, model_dir)
        if path:
            generated.append(path)

    return model_dir
