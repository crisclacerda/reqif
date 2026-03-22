"""CLI entry points for reqif.specir.

Usage::

    python -m reqif.specir import --input file.reqif --db specir.db [--spec-id slug]
    python -m reqif.specir export --db specir.db --output file.reqif [--spec-id slug]
    python -m reqif.specir decompile --db specir.db --output-dir ./project [--spec-id slug]
    python -m reqif.specir import-decompile --input file.reqif --output-dir ./project [--spec-id slug]
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys


def _cmd_import(args: argparse.Namespace) -> int:
    from reqif.parser import ReqIFParser

    from .importer import import_reqif

    input_path = os.path.abspath(args.input)
    db_path = os.path.abspath(args.db)

    bundle = ReqIFParser.parse(input_path)
    if bundle.exceptions:
        for exc in bundle.exceptions:
            print(f"warning: {exc}", file=sys.stderr)

    conn = sqlite3.connect(db_path)
    try:
        spec_id = import_reqif(bundle, conn, spec_slug=args.spec_id)
        print(f"Imported into: {db_path}")
        print(f"Specification: {spec_id}")
    finally:
        conn.close()
    return 0


def _resolve_spec_id(conn: sqlite3.Connection, spec_id: str | None) -> str | None:
    """Resolve spec_id: return it if given, auto-detect if single spec, else error."""
    if spec_id is not None:
        return spec_id
    rows = conn.execute(
        "SELECT identifier FROM specifications ORDER BY identifier"
    ).fetchall()
    ids = [str(r[0]) for r in rows]
    if not ids:
        print("error: no specifications found in DB.", file=sys.stderr)
        return None
    if len(ids) != 1:
        print(
            f"error: DB has multiple specifications: {ids}. Provide --spec-id.",
            file=sys.stderr,
        )
        return None
    return ids[0]


def _cmd_export(args: argparse.Namespace) -> int:
    from reqif.unparser import ReqIFUnparser

    from .exporter import export_reqif

    db_path = os.path.abspath(args.db)
    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        spec_id = _resolve_spec_id(conn, args.spec_id)
        if spec_id is None:
            return 2

        bundle = export_reqif(conn, spec_id)
    finally:
        conn.close()

    xml = ReqIFUnparser.unparse(bundle)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"Wrote ReqIF: {out_path}")
    print(f"Specification: {spec_id}")
    return 0


def _cmd_decompile(args: argparse.Namespace) -> int:
    from .decompiler import decompile
    from .model_generator import generate_model
    from .project_generator import generate_project

    db_path = os.path.abspath(args.db)
    out_dir = os.path.abspath(args.output_dir)
    model_name = args.model_name

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        spec_id = _resolve_spec_id(conn, args.spec_id)
        if spec_id is None:
            return 2

        # Generate Lua model types.
        model_dir = generate_model(conn, out_dir, model_name)
        print(f"Model types: {model_dir}")

        # Generate CommonSpec markdown.
        md_files = decompile(
            conn, spec_id, out_dir,
            children_threshold=args.threshold,
            overwrite=args.overwrite,
        )
        for f in md_files:
            print(f"Wrote: {f}")

        # Generate project.yaml.
        doc_files = [os.path.relpath(f, out_dir) for f in md_files if f.endswith(".md")]
        # Only list root files (not child includes) in doc_files.
        root_files = [f for f in doc_files if os.sep not in f and "/" not in f]
        proj_path = generate_project(
            conn, spec_id, out_dir,
            model_name=model_name,
            doc_files=root_files or doc_files,
            overwrite=args.overwrite,
        )
        print(f"Project: {proj_path}")
    finally:
        conn.close()
    return 0


def _cmd_import_decompile(args: argparse.Namespace) -> int:
    from reqif.parser import ReqIFParser

    from .decompiler import decompile
    from .importer import import_reqif
    from .model_generator import generate_model
    from .project_generator import generate_project

    input_path = os.path.abspath(args.input)
    out_dir = os.path.abspath(args.output_dir)
    model_name = args.model_name
    db_path = os.path.join(out_dir, ".specir.db")

    # Parse ReqIF.
    bundle = ReqIFParser.parse(input_path)
    if bundle.exceptions:
        for exc in bundle.exceptions:
            print(f"warning: {exc}", file=sys.stderr)

    # Import into SpecIR.
    os.makedirs(out_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        spec_id = import_reqif(bundle, conn, spec_slug=args.spec_id)
        print(f"Imported: {spec_id}")

        # Generate model + markdown + project.
        model_dir = generate_model(conn, out_dir, model_name)
        print(f"Model types: {model_dir}")

        md_files = decompile(
            conn, spec_id, out_dir,
            children_threshold=args.threshold,
            overwrite=args.overwrite,
        )
        for f in md_files:
            print(f"Wrote: {f}")

        doc_files = [os.path.relpath(f, out_dir) for f in md_files if f.endswith(".md")]
        root_files = [f for f in doc_files if os.sep not in f and "/" not in f]
        proj_path = generate_project(
            conn, spec_id, out_dir,
            model_name=model_name,
            doc_files=root_files or doc_files,
            overwrite=args.overwrite,
        )
        print(f"Project: {proj_path}")
    finally:
        conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m reqif.specir",
        description="ReqIF ↔ SpecIR interoperability CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # import
    p_import = sub.add_parser("import", help="Import a .reqif file into a SpecIR database")
    p_import.add_argument("--input", required=True, help="Path to .reqif file")
    p_import.add_argument("--db", required=True, help="Path to SpecIR SQLite database (created if needed)")
    p_import.add_argument("--spec-id", default=None, help="Override the specification identifier")

    # export
    p_export = sub.add_parser("export", help="Export a SpecIR specification to .reqif")
    p_export.add_argument("--db", required=True, help="Path to SpecIR SQLite database")
    p_export.add_argument("--output", required=True, help="Output .reqif file path")
    p_export.add_argument("--spec-id", default=None, help="Specification identifier to export")

    # decompile
    p_decompile = sub.add_parser("decompile", help="Decompile SpecIR into a CommonSpec project")
    p_decompile.add_argument("--db", required=True, help="Path to SpecIR SQLite database")
    p_decompile.add_argument("--output-dir", required=True, help="Output project directory")
    p_decompile.add_argument("--spec-id", default=None, help="Specification identifier")
    p_decompile.add_argument("--model-name", default="imported", help="Model name (default: imported)")
    p_decompile.add_argument("--threshold", type=int, default=50, help="Object count threshold for file splitting")
    p_decompile.add_argument("--overwrite", action="store_true", help="Overwrite existing files")

    # import-decompile (combined)
    p_id = sub.add_parser("import-decompile", help="Import .reqif and decompile to CommonSpec project")
    p_id.add_argument("--input", required=True, help="Path to .reqif file")
    p_id.add_argument("--output-dir", required=True, help="Output project directory")
    p_id.add_argument("--spec-id", default=None, help="Override the specification identifier")
    p_id.add_argument("--model-name", default="imported", help="Model name (default: imported)")
    p_id.add_argument("--threshold", type=int, default=50, help="Object count threshold for file splitting")
    p_id.add_argument("--overwrite", action="store_true", help="Overwrite existing files")

    args = parser.parse_args()
    if args.command == "import":
        return _cmd_import(args)
    elif args.command == "export":
        return _cmd_export(args)
    elif args.command == "decompile":
        return _cmd_decompile(args)
    elif args.command == "import-decompile":
        return _cmd_import_decompile(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
