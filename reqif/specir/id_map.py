"""Round-trip ID mapping between SpecIR and ReqIF identifiers.

Stores mappings in a ``_reqif_id_map`` table (tool-specific, prefixed with
underscore to distinguish from core SpecIR tables).  On first export the
table is populated with deterministic SHA1-based IDs; on re-export after
an import the original ReqIF identifiers are reused.
"""
from __future__ import annotations

import hashlib
import sqlite3
from typing import Optional, Tuple

_DDL = """\
CREATE TABLE IF NOT EXISTS _reqif_id_map (
    specir_table TEXT NOT NULL,
    specir_id    TEXT NOT NULL,
    reqif_id     TEXT NOT NULL,
    PRIMARY KEY (specir_table, specir_id),
    UNIQUE (reqif_id)
);
"""


def _stable_id(prefix: str, value: str) -> str:
    """Generate a deterministic ReqIF identifier from *prefix* and *value*.

    Matches the convention used by the original ``reqif_export.py``.
    """
    h = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"_{prefix}-{h}"


class IdMap:
    """Bidirectional ID mapping backed by ``_reqif_id_map``."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        conn.executescript(_DDL)

    # -- write ----------------------------------------------------------

    def put(self, table: str, specir_id: str, reqif_id: str) -> None:
        """Record a mapping (insert or replace)."""
        self._conn.execute(
            "INSERT OR REPLACE INTO _reqif_id_map (specir_table, specir_id, reqif_id) "
            "VALUES (?, ?, ?)",
            (table, str(specir_id), reqif_id),
        )

    # -- read -----------------------------------------------------------

    def get_reqif_id(self, table: str, specir_id: str) -> Optional[str]:
        """Look up a ReqIF identifier for a SpecIR row (used by exporter)."""
        row = self._conn.execute(
            "SELECT reqif_id FROM _reqif_id_map WHERE specir_table = ? AND specir_id = ?",
            (table, str(specir_id)),
        ).fetchone()
        return row[0] if row else None

    def get_specir_id(self, reqif_id: str) -> Optional[Tuple[str, str]]:
        """Look up a SpecIR (table, id) for a ReqIF identifier (used by importer)."""
        row = self._conn.execute(
            "SELECT specir_table, specir_id FROM _reqif_id_map WHERE reqif_id = ?",
            (reqif_id,),
        ).fetchone()
        return (row[0], row[1]) if row else None

    # -- convenience ----------------------------------------------------

    def ensure_reqif_id(self, table: str, specir_id: str, prefix: str) -> str:
        """Return existing ReqIF ID or generate and store a stable one."""
        existing = self.get_reqif_id(table, specir_id)
        if existing is not None:
            return existing
        new_id = _stable_id(prefix, str(specir_id))
        self.put(table, specir_id, new_id)
        return new_id
