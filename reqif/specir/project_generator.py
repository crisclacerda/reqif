"""Generate a project.yaml for a decompiled SpecIR specification."""
from __future__ import annotations

import os
import re
import sqlite3
import sys
from typing import List, Optional


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-") or "untitled"


def generate_project(
    conn: sqlite3.Connection,
    spec_id: str,
    output_dir: str,
    model_name: str = "imported",
    doc_files: Optional[List[str]] = None,
    overwrite: bool = False,
) -> str:
    """Generate ``project.yaml`` for a decompiled specification.

    Parameters
    ----------
    conn : sqlite3.Connection
        Open connection.
    spec_id : str
        Specification identifier.
    output_dir : str
        Directory where ``project.yaml`` is written.
    model_name : str
        Model template name (default: ``"imported"``).
    doc_files : list[str], optional
        Explicit doc file list. If None, auto-detected from spec.
    overwrite : bool
        Overwrite existing file.

    Returns
    -------
    str
        Path to the generated ``project.yaml``.
    """
    conn.row_factory = sqlite3.Row
    spec_row = conn.execute(
        "SELECT identifier, long_name FROM specifications WHERE identifier = ?",
        (spec_id,),
    ).fetchone()

    long_name = (spec_row["long_name"] if spec_row and spec_row["long_name"] else None) or spec_id
    project_code = spec_id.upper().replace("-", "_").replace(" ", "_")
    spec_slug = _slugify(long_name or spec_id)

    if doc_files is None:
        doc_files = [f"{spec_slug}.md"]

    doc_files_yaml = "\n".join(f"  - {f}" for f in doc_files)

    content = f"""\
# Generated from ReqIF import
project:
  code: {project_code}
  name: {long_name}

template: {model_name}

output_dir: build/

doc_files:
{doc_files_yaml}

outputs:
  - format: docx
    path: build/docx/{spec_id}.docx
  - format: html5
    path: build/www/{spec_id}.html

html5:
  number_sections: true
  table_of_contents: true
  toc_depth: 3
  standalone: true
  embed_resources: true
"""

    path = os.path.join(output_dir, "project.yaml")
    if os.path.exists(path) and not overwrite:
        print(f"skip (exists): {path}", file=sys.stderr)
        return path

    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
