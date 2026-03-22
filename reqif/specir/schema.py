"""SpecIR core schema DDL for standalone databases.

Embeds the minimal SpecIR DDL (type system + content tables) so that a
ReqIF import can create a valid SpecIR database from scratch.  Non-core
tables (build_graph, source_files, output_cache, FTS) are excluded.

Authoritative source:
  - src/db/schema/types.lua   (type system)
  - src/db/schema/content.lua (content)
"""
from __future__ import annotations

import sqlite3

# ---------------------------------------------------------------------------
# Type system DDL (from src/db/schema/types.lua, CREATE TABLE only)
# ---------------------------------------------------------------------------
_TYPE_SYSTEM_DDL = """\
CREATE TABLE IF NOT EXISTS spec_object_types (
  identifier   TEXT PRIMARY KEY,
  long_name    TEXT NOT NULL UNIQUE,
  description  TEXT,
  extends      TEXT,
  is_composite INTEGER DEFAULT 0,
  is_required  INTEGER DEFAULT 0,
  is_default   INTEGER DEFAULT 0,
  pid_prefix   TEXT,
  pid_format   TEXT DEFAULT '%s-%03d',
  aliases      TEXT
);

CREATE TABLE IF NOT EXISTS spec_float_types (
  identifier            TEXT PRIMARY KEY,
  long_name             TEXT NOT NULL UNIQUE,
  description           TEXT,
  caption_format        TEXT,
  counter_group         TEXT,
  aliases               TEXT,
  needs_external_render INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS spec_relation_types (
  identifier       TEXT PRIMARY KEY,
  long_name        TEXT NOT NULL UNIQUE,
  description      TEXT,
  extends          TEXT,
  source_type_ref  TEXT,
  target_type_ref  TEXT,
  link_selector    TEXT,
  source_attribute TEXT,
  FOREIGN KEY (source_type_ref) REFERENCES spec_object_types(identifier),
  FOREIGN KEY (target_type_ref) REFERENCES spec_object_types(identifier)
);

CREATE TABLE IF NOT EXISTS spec_view_types (
  identifier            TEXT PRIMARY KEY,
  long_name             TEXT NOT NULL UNIQUE,
  description           TEXT,
  counter_group         TEXT,
  aliases               TEXT,
  inline_prefix         TEXT,
  materializer_type     TEXT,
  view_subtype_ref      TEXT,
  needs_external_render INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS datatype_definitions (
  identifier TEXT PRIMARY KEY,
  long_name  TEXT NOT NULL UNIQUE,
  type       TEXT NOT NULL CHECK (type IN ('STRING','INTEGER','BOOLEAN','DATE','REAL','ENUM','XHTML'))
);

CREATE TABLE IF NOT EXISTS spec_attribute_types (
  identifier     TEXT PRIMARY KEY,
  owner_type_ref TEXT NOT NULL,
  long_name      TEXT NOT NULL,
  datatype_ref   TEXT NOT NULL,
  min_occurs     INTEGER DEFAULT 0,
  max_occurs     INTEGER DEFAULT 1,
  min_value      REAL,
  max_value      REAL,
  FOREIGN KEY (datatype_ref) REFERENCES datatype_definitions(identifier),
  UNIQUE (owner_type_ref, long_name)
);

CREATE TABLE IF NOT EXISTS enum_values (
  identifier   TEXT PRIMARY KEY,
  datatype_ref TEXT NOT NULL,
  key          TEXT NOT NULL,
  sequence     INTEGER DEFAULT 0,
  FOREIGN KEY (datatype_ref) REFERENCES datatype_definitions(identifier)
);

CREATE TABLE IF NOT EXISTS implicit_type_aliases (
  alias          TEXT PRIMARY KEY COLLATE NOCASE,
  object_type_id TEXT NOT NULL,
  FOREIGN KEY (object_type_id) REFERENCES spec_object_types(identifier)
);

CREATE TABLE IF NOT EXISTS implicit_spec_type_aliases (
  alias        TEXT PRIMARY KEY COLLATE NOCASE,
  spec_type_id TEXT NOT NULL,
  FOREIGN KEY (spec_type_id) REFERENCES spec_specification_types(identifier)
);

CREATE TABLE IF NOT EXISTS spec_specification_types (
  identifier  TEXT PRIMARY KEY,
  long_name   TEXT NOT NULL UNIQUE,
  description TEXT,
  extends     TEXT,
  is_default  INTEGER DEFAULT 0
);
"""

# ---------------------------------------------------------------------------
# Content DDL (from src/db/schema/content.lua, CREATE TABLE + indexes)
# ---------------------------------------------------------------------------
_CONTENT_DDL = """\
CREATE TABLE IF NOT EXISTS specifications (
  identifier TEXT PRIMARY KEY,
  root_path  TEXT NOT NULL UNIQUE,
  long_name  TEXT,
  type_ref   TEXT,
  pid        TEXT,
  header_ast JSON,
  body_ast   JSON
);

CREATE TABLE IF NOT EXISTS spec_objects (
  id                 INTEGER PRIMARY KEY,
  content_sha        TEXT,
  specification_ref  TEXT NOT NULL,
  type_ref           TEXT NOT NULL,
  from_file          TEXT NOT NULL,
  file_seq           INTEGER NOT NULL,
  pid                TEXT,
  pid_prefix         TEXT,
  pid_sequence       INTEGER,
  pid_auto_generated INTEGER DEFAULT 0,
  title_text         TEXT NOT NULL,
  label              TEXT,
  level              INTEGER,
  start_line         INTEGER,
  end_line           INTEGER,
  ast                JSON,
  content_xhtml      TEXT,
  FOREIGN KEY (specification_ref) REFERENCES specifications(identifier),
  FOREIGN KEY (type_ref) REFERENCES spec_object_types(identifier)
);

CREATE TABLE IF NOT EXISTS spec_floats (
  id                INTEGER PRIMARY KEY,
  content_sha       TEXT,
  specification_ref TEXT NOT NULL,
  type_ref          TEXT NOT NULL,
  from_file         TEXT NOT NULL,
  file_seq          INTEGER NOT NULL,
  start_line        INTEGER,
  label             TEXT NOT NULL,
  number            INTEGER,
  caption           TEXT,
  pandoc_attributes JSON,
  raw_content       TEXT,
  raw_ast           JSON,
  resolved_ast      JSON,
  parent_object_id  INTEGER,
  anchor            TEXT,
  syntax_key        TEXT,
  FOREIGN KEY (specification_ref) REFERENCES specifications(identifier),
  FOREIGN KEY (type_ref) REFERENCES spec_float_types(identifier),
  FOREIGN KEY (parent_object_id) REFERENCES spec_objects(id)
);

CREATE TABLE IF NOT EXISTS spec_relations (
  id                INTEGER PRIMARY KEY,
  content_sha       TEXT,
  specification_ref TEXT NOT NULL,
  source_object_id  INTEGER NOT NULL,
  target_text       TEXT,
  target_object_id  INTEGER,
  target_float_id   INTEGER,
  type_ref          TEXT,
  is_ambiguous      INTEGER DEFAULT 0,
  from_file         TEXT NOT NULL,
  link_line         INTEGER DEFAULT 0,
  source_attribute  TEXT,
  link_selector     TEXT,
  FOREIGN KEY (specification_ref) REFERENCES specifications(identifier),
  FOREIGN KEY (source_object_id) REFERENCES spec_objects(id),
  FOREIGN KEY (target_object_id) REFERENCES spec_objects(id),
  FOREIGN KEY (target_float_id) REFERENCES spec_floats(id),
  FOREIGN KEY (type_ref) REFERENCES spec_relation_types(identifier)
);

CREATE TABLE IF NOT EXISTS spec_views (
  id                INTEGER PRIMARY KEY,
  content_sha       TEXT,
  specification_ref TEXT NOT NULL,
  view_type_ref     TEXT NOT NULL,
  from_file         TEXT NOT NULL,
  file_seq          INTEGER NOT NULL,
  start_line        INTEGER,
  raw_ast           JSON,
  resolved_ast      JSON,
  resolved_data     JSON,
  FOREIGN KEY (specification_ref) REFERENCES specifications(identifier),
  FOREIGN KEY (view_type_ref) REFERENCES spec_view_types(identifier)
);

CREATE TABLE IF NOT EXISTS spec_attribute_values (
  id                INTEGER PRIMARY KEY,
  content_sha       TEXT,
  specification_ref TEXT NOT NULL,
  owner_object_id   INTEGER,
  owner_float_id    INTEGER,
  name              TEXT NOT NULL,
  raw_value         TEXT,
  string_value      TEXT,
  int_value         INTEGER,
  real_value        REAL,
  bool_value        INTEGER,
  date_value        TEXT,
  enum_ref          TEXT,
  ast               JSON,
  datatype          TEXT NOT NULL,
  xhtml_value       TEXT,
  FOREIGN KEY (specification_ref) REFERENCES specifications(identifier),
  FOREIGN KEY (owner_object_id) REFERENCES spec_objects(id),
  FOREIGN KEY (owner_float_id) REFERENCES spec_floats(id),
  FOREIGN KEY (enum_ref) REFERENCES enum_values(identifier)
);

CREATE INDEX IF NOT EXISTS idx_objects_spec_pid
    ON spec_objects(specification_ref, pid) WHERE pid IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_objects_spec_label
    ON spec_objects(specification_ref, label) WHERE label IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_floats_spec_label
    ON spec_floats(specification_ref, label) WHERE label IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_spec_objects_spec_type
    ON spec_objects(specification_ref, type_ref, file_seq);
CREATE INDEX IF NOT EXISTS idx_spec_objects_pid
    ON spec_objects(pid) WHERE pid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_spec_objects_spec_fileseq
    ON spec_objects(specification_ref, file_seq);
CREATE INDEX IF NOT EXISTS idx_spec_relations_source
    ON spec_relations(source_object_id, type_ref);
CREATE INDEX IF NOT EXISTS idx_spec_relations_target_obj
    ON spec_relations(target_object_id, type_ref);
CREATE INDEX IF NOT EXISTS idx_spec_attr_owner_name
    ON spec_attribute_values(owner_object_id, name);
CREATE INDEX IF NOT EXISTS idx_spec_attribute_values_spec
    ON spec_attribute_values(specification_ref);
CREATE INDEX IF NOT EXISTS idx_attr_def_owner_type
    ON spec_attribute_types(owner_type_ref);
CREATE INDEX IF NOT EXISTS idx_enum_values_datatype
    ON enum_values(datatype_ref);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create all core SpecIR tables if they do not already exist."""
    conn.executescript(_TYPE_SYSTEM_DDL)
    conn.executescript(_CONTENT_DDL)


def clear_content(conn: sqlite3.Connection, spec_id: str) -> None:
    """Delete all content rows for a given specification (for re-import)."""
    for table in (
        "spec_attribute_values",
        "spec_relations",
        "spec_views",
        "spec_floats",
        "spec_objects",
        "specifications",
    ):
        conn.execute(
            f"DELETE FROM {table} WHERE specification_ref = ?",  # noqa: S608
            (spec_id,),
        )
    # specifications PK is 'identifier', not 'specification_ref'
    conn.execute("DELETE FROM specifications WHERE identifier = ?", (spec_id,))
