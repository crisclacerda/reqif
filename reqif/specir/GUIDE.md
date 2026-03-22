# reqif.specir — ReqIF Interoperability Guide

## Overview

`reqif.specir` is a Python package that provides bidirectional conversion between
ReqIF (Requirements Interchange Format) and SpecCompiler's ecosystem. It enables:

- **Import**: Parse `.reqif` files into SpecIR (SQLite intermediate representation)
- **Export**: Generate valid `.reqif` from SpecIR databases
- **Decompile**: Convert SpecIR into editable CommonSpec markdown projects

The package lives at `dist/vendor/python/reqif/specir/` and is invoked via:

```
python -m reqif.specir <command> [options]
```

## Architecture

```
┌─────────────┐    import     ┌─────────┐    decompile    ┌──────────────┐
│  .reqif     │ ───────────> │  SpecIR  │ ────────────>  │  CommonSpec  │
│  (XML)      │ <─────────── │ (SQLite) │                │  project     │
└─────────────┘    export     └─────────┘                └──────────────┘
                                  │
                                  │ decompile generates:
                                  ├── models/{name}/types/*.lua
                                  ├── {spec-slug}.md  (+ child files)
                                  └── project.yaml
```

### Module Map

| Module | Purpose |
|--------|---------|
| `importer.py` | ReqIF bundle → SpecIR tables |
| `exporter.py` | SpecIR tables → ReqIF bundle |
| `decompiler.py` | SpecIR content → CommonSpec markdown |
| `model_generator.py` | SpecIR types → Lua type definitions |
| `project_generator.py` | Generate `project.yaml` configuration |
| `content_converter.py` | Pandoc AST / HTML → Markdown / HTML |
| `schema.py` | SpecIR SQLite schema definition |
| `id_map.py` | Stable ReqIF ID generation for round-trips |
| `xhtml.py` | ReqIF XHTML namespace conversion |
| `cli.py` | Command-line interface |

---

## Quick Start

### Import a ReqIF file and create an editable project

```bash
# One command: import + decompile into a project directory
python -m reqif.specir import-decompile \
    --input requirements.reqif \
    --output-dir ./my_project \
    --overwrite

# Result:
# my_project/
# ├── project.yaml              # SpecCompiler project config
# ├── models/imported/types/    # Lua type definitions
# │   ├── objects/requirement.lua
# │   ├── relations/traces_to.lua
# │   └── specifications/srs.lua
# └── my-spec.md                # CommonSpec markdown
```

### Export SpecIR back to ReqIF

```bash
# Two-step: import then export
python -m reqif.specir import --input original.reqif --db specir.db
python -m reqif.specir export --db specir.db --output exported.reqif
```

### Decompile an existing SpecIR database

```bash
# If you already have a specir.db (e.g., from `specc build`)
python -m reqif.specir decompile \
    --db build/specir.db \
    --output-dir ./project \
    --spec-id srs \
    --overwrite
```

---

## CLI Reference

### `import` — Import ReqIF into SpecIR

```
python -m reqif.specir import --input FILE --db DB [--spec-id ID]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--input` | Yes | Path to `.reqif` file |
| `--db` | Yes | SQLite database path (created if needed) |
| `--spec-id` | No | Override auto-detected specification identifier |

### `export` — Export SpecIR to ReqIF

```
python -m reqif.specir export --db DB --output FILE [--spec-id ID]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--db` | Yes | SpecIR SQLite database |
| `--output` | Yes | Output `.reqif` file path |
| `--spec-id` | No | Specification to export (auto-detected if only one) |

### `decompile` — Decompile SpecIR to CommonSpec project

```
python -m reqif.specir decompile --db DB --output-dir DIR [options]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--db` | Yes | | SpecIR SQLite database |
| `--output-dir` | Yes | | Output project directory |
| `--spec-id` | No | auto | Specification identifier |
| `--model-name` | No | `imported` | Name for the generated Lua model |
| `--threshold` | No | `50` | Object count threshold for file splitting |
| `--overwrite` | No | false | Overwrite existing files |

### `import-decompile` — Import + Decompile in one step

```
python -m reqif.specir import-decompile --input FILE --output-dir DIR [options]
```

Combines `import` and `decompile`. Same options as `decompile` plus `--input`.
The SpecIR database is stored as `.specir.db` inside the output directory.

---

## Data Model: How Content Maps Between Formats

### Specification hierarchy

```
ReqIF                        SpecIR                      CommonSpec
──────                       ──────                      ──────────
SPECIFICATION           →    specifications table    →   # TYPE: Title @PID
  SPEC-HIERARCHY        →    spec_objects (level)    →   ## TYPE: Title @PID
    SPEC-OBJECT         →    spec_objects row        →   Heading + body + attrs
      ATTRIBUTE-VALUE   →    spec_attribute_values   →   > name: value
  SPEC-RELATION         →    spec_relations          →   [target](@)
```

### Core pseudo-attributes

These ReqIF pseudo-attributes map to **dedicated SpecIR columns**, not to
the EAV attribute table:

| ReqIF Attribute | SpecIR Column | CommonSpec |
|-----------------|---------------|------------|
| `ReqIF.ForeignID` | `spec_objects.pid` | `@PID` suffix in heading |
| `ReqIF.Name` | `spec_objects.title_text` | Heading text |
| `ReqIF.Text` | `spec_objects.content_xhtml` | Body content (below heading) |

### Body content storage

Body content has two representations in SpecIR:

| Column | Source | Format |
|--------|--------|--------|
| `spec_objects.content_xhtml` | ReqIF importer | HTML5 fragment |
| `spec_objects.ast` | SpecCompiler build | Pandoc AST JSON |

The conversion layer (`content_converter.py`) handles both:

- **Decompiler** (SpecIR → Markdown): prefers `ast`, falls back to `content_xhtml`
- **Exporter** (SpecIR → ReqIF): prefers `content_xhtml`, falls back to `ast` → HTML

### Attribute value types

| SpecIR Datatype | ReqIF Element | CommonSpec Syntax |
|-----------------|---------------|-------------------|
| `STRING` | `ATTRIBUTE-VALUE-STRING` | `> name: text` |
| `INTEGER` | `ATTRIBUTE-VALUE-INTEGER` | `> name: 42` |
| `REAL` | `ATTRIBUTE-VALUE-REAL` | `> name: 3.14` |
| `BOOLEAN` | `ATTRIBUTE-VALUE-BOOLEAN` | `> name: true` |
| `DATE` | `ATTRIBUTE-VALUE-DATE` | `> name: 2024-01-15` |
| `ENUM` | `ATTRIBUTE-VALUE-ENUMERATION` | `> name: Approved` |
| `XHTML` | `ATTRIBUTE-VALUE-XHTML` | `> name: Rich **text**` |

---

## Generated Output Examples

### CommonSpec markdown (single file)

```markdown
# REQUIREMENT_SPECIFICATION: My Requirements @SPEC-001

> version: 1.0

## REQUIREMENT: User Authentication @REQ-001

> status: Approved
> priority: High

The system shall authenticate users via OAuth 2.0 before granting
access to protected resources.

[REQ-002](@)

## REQUIREMENT: Password Policy @REQ-002

> status: Draft
> priority: Medium

Passwords must be at least 12 characters and include uppercase,
lowercase, numeric, and special characters.
```

### CommonSpec markdown (multi-file, threshold exceeded)

Root file `my-spec.md`:
```markdown
# SPEC: My Large Specification @SPEC-001

> version: 2.0

```{.include}
my-spec/authentication.md
my-spec/authorization.md
my-spec/audit.md
```
```

Child file `my-spec/authentication.md`:
```markdown
## REQUIREMENT: User Login @REQ-001

> status: Approved

The system shall provide a login page...

### REQUIREMENT: SSO Integration @REQ-001-001

> status: Draft

Single sign-on via SAML 2.0...
```

### Lua type definition

```lua
local M = {}

M.object = {
    id = "REQUIREMENT",
    long_name = "Requirement",
    description = "Imported from ReqIF",
    pid_prefix = "REQ",
    attributes = {
        { name = "status", type = "ENUM", values = { "Draft", "Approved", "Obsolete" } },
        { name = "priority", type = "ENUM", values = { "High", "Medium", "Low" } },
        { name = "rationale", type = "XHTML" },
    }
}

return M
```

### project.yaml

```yaml
project:
  code: MY_SPEC
  name: My Requirements

template: imported

output_dir: build/

doc_files:
  - my-spec.md

outputs:
  - format: docx
    path: build/docx/my-spec.docx
  - format: html5
    path: build/www/my-spec.html
```

---

## Python API

All functions are available from the top-level package:

```python
from reqif.specir import (
    import_reqif,
    export_reqif,
    decompile,
    generate_model,
    generate_project,
)
```

### `import_reqif(bundle, conn, spec_slug=None) -> str`

Import a parsed ReqIF bundle into a SpecIR database.

```python
from reqif.parser import ReqIFParser
from reqif.specir import import_reqif
import sqlite3

bundle = ReqIFParser.parse("requirements.reqif")
conn = sqlite3.connect("specir.db")
spec_id = import_reqif(bundle, conn)
print(f"Imported specification: {spec_id}")
conn.close()
```

**Parameters:**
- `bundle` — `ReqIFBundle` from `ReqIFParser.parse()`
- `conn` — Open `sqlite3.Connection` (schema is created automatically)
- `spec_slug` — Override the auto-detected specification identifier

**Returns:** The specification identifier string.

### `export_reqif(conn, spec_id) -> ReqIFBundle`

Export a SpecIR specification to a ReqIF bundle.

```python
from reqif.unparser import ReqIFUnparser
from reqif.specir import export_reqif
import sqlite3

conn = sqlite3.connect("specir.db")
conn.row_factory = sqlite3.Row
bundle = export_reqif(conn, "srs")
xml = ReqIFUnparser.unparse(bundle)

with open("exported.reqif", "w") as f:
    f.write(xml)
conn.close()
```

**Parameters:**
- `conn` — Open `sqlite3.Connection` with `row_factory = sqlite3.Row`
- `spec_id` — Specification identifier to export

**Returns:** `ReqIFBundle` ready for `ReqIFUnparser.unparse()`.

### `decompile(conn, spec_id, output_dir, *, children_threshold=50, overwrite=False) -> list[str]`

Decompile a SpecIR specification into CommonSpec markdown files.

```python
from reqif.specir import decompile
import sqlite3

conn = sqlite3.connect("specir.db")
conn.row_factory = sqlite3.Row
files = decompile(conn, "srs", "./output", overwrite=True)
for f in files:
    print(f"Generated: {f}")
conn.close()
```

**Parameters:**
- `conn` — Open `sqlite3.Connection` with `row_factory = sqlite3.Row`
- `spec_id` — Specification identifier
- `output_dir` — Directory for generated `.md` files
- `children_threshold` — If object count exceeds this, split into multiple files
- `overwrite` — If `True`, overwrite existing files; otherwise skip them

**Returns:** List of generated file paths.

### `generate_model(conn, output_dir, model_name="imported") -> str`

Generate Lua type definitions from SpecIR type system.

```python
from reqif.specir import generate_model
import sqlite3

conn = sqlite3.connect("specir.db")
model_dir = generate_model(conn, "./output", "imported")
print(f"Model at: {model_dir}")
conn.close()
```

**Returns:** Path to the generated model directory.

### `generate_project(conn, spec_id, output_dir, *, model_name="imported", doc_files=None, overwrite=False) -> str`

Generate a `project.yaml` configuration file.

```python
from reqif.specir import generate_project
import sqlite3

conn = sqlite3.connect("specir.db")
path = generate_project(conn, "srs", "./output",
                        model_name="imported",
                        doc_files=["my-spec.md"])
print(f"Project config: {path}")
conn.close()
```

**Returns:** Path to the generated `project.yaml`.

---

## End-to-End Workflows

### Workflow 1: Import third-party ReqIF → Edit → Build

```bash
# 1. Import and create an editable project
python -m reqif.specir import-decompile \
    --input vendor_requirements.reqif \
    --output-dir ./vendor_project \
    --overwrite

# 2. Edit the generated markdown files
#    (e.g., add traceability links, update attributes)

# 3. Build with SpecCompiler
cd vendor_project
specc build
```

### Workflow 2: Round-trip — Import, modify in SpecIR, re-export

```bash
# 1. Import
python -m reqif.specir import \
    --input original.reqif \
    --db work.db

# 2. Modify via SQL (e.g., bulk status update)
sqlite3 work.db "UPDATE spec_attribute_values SET raw_value='Approved' \
    WHERE name='status' AND raw_value='Draft'"

# 3. Export back to ReqIF
python -m reqif.specir export \
    --db work.db \
    --output updated.reqif
```

### Workflow 3: Export SpecCompiler project to ReqIF

```bash
# 1. Build your SpecCompiler project (creates specir.db)
cd my_project
specc build

# 2. Export the built SpecIR to ReqIF
python -m reqif.specir export \
    --db build/specir.db \
    --output build/export.reqif \
    --spec-id srs
```

Body content stored as Pandoc AST (from `specc build`) is automatically
converted to HTML for the ReqIF export.

### Workflow 4: StrictDoc interop (SDoc ↔ ReqIF ↔ CommonSpec)

Two directions are supported via [StrictDoc](https://github.com/strictdoc-project/strictdoc) as a bridge:

**Direction A — SDoc → CommonSpec** (import third-party StrictDoc projects):

```bash
# 1. Export StrictDoc project to ReqIF
strictdoc export ./sdoc_project \
    --formats=reqif-sdoc \
    --output-dir ./export_out \
    --no-parallelization

# 2. Import the ReqIF and decompile to CommonSpec
python -m reqif.specir import-decompile \
    --input ./export_out/reqif/*.reqif \
    --output-dir ./commonspec_project \
    --overwrite
```

**Direction B — SpecCompiler → SDoc** (share with StrictDoc users):

```bash
# 1. Build SpecCompiler project (creates specir.db)
specc build

# 2. Export to ReqIF
python -m reqif.specir export \
    --db build/specir.db \
    --output build/export.reqif \
    --spec-id srs

# 3. Import into StrictDoc
strictdoc import reqif p01_sdoc build/export.reqif ./sdoc_output
```

**Persisted artifacts**: The stress tests write intermediate files to
`tests/fixtures/interop/` for manual inspection:

| Directory | Contents |
|-----------|----------|
| `sdoc_to_commonspec/input/` | StrictDoc L2 requirements `.sdoc` (179 UIDs, external refs stripped) |
| `sdoc_to_commonspec/reqif/` | ReqIF exported by StrictDoc (~400KB) |
| `sdoc_to_commonspec/commonspec/` | CommonSpec `.md` decompiled from SpecIR (17 files) |
| `strictdoc_docs/` | Original StrictDoc `.sdoc` source files (L1, L2, L3, user guide, etc.) |
| `engineering_round_trip/reqif/` | ReqIF exported from engineering DB |
| `engineering_round_trip/commonspec/` | CommonSpec `.md` after round-trip |
| `engineering_sdoc/sdoc/` | `.sdoc` files generated by StrictDoc from our ReqIF |

These artifacts are regenerated on every test run. To inspect them without
running the full suite:

```bash
PYTHONPATH=dist/vendor/python python3 -m unittest \
    reqif.specir.tests.test_interop_stress -v
ls -R dist/vendor/python/reqif/specir/tests/fixtures/interop/
```

**Known StrictDoc limitations**:
- StrictDoc's importer may generate empty multiline blocks (`>>>\n<<<`) that
  its own parser rejects on re-export.
- Multiple SpecIR relation types mapping to the same StrictDoc "Parent" role
  can cause duplicate relation errors on re-export. One-way import works fine.

---

## Content Conversion Details

### AST → Markdown pipeline (decompiler)

When decompiling from a SpecCompiler-built database, body content is stored
as Pandoc AST JSON in `spec_objects.ast`. The conversion pipeline:

1. **Parse** JSON block list
2. **Strip noise**: Remove `data-pos` and `data-source-file` key-value pairs
3. **Unwrap structural Divs**: Remove `spec-object`, `spec-object-body`,
   `spec-object-attributes`, `spec-object-relations` wrapper Divs (recursively,
   including inside list items)
4. **Strip duplicate content**: Remove Header blocks (decompiler renders its own),
   DefinitionList/BlockQuote blocks (attributes already in EAV table),
   and standalone relation link paragraphs (`[target](@)`)
5. **Merge fragmented Plains**: Consolidate consecutive Plain blocks
   (common in attribute ASTs where each inline is a separate block)
6. **Convert via Pandoc**: `pandoc -f json -t markdown --wrap=none`
7. **Post-clean**: Remove residual `<div>` tags, collapse blank lines

### HTML → Markdown (decompiler, ReqIF-imported data)

For ReqIF-imported data, `content_xhtml` stores HTML5 fragments.
Conversion: `pandoc -f html -t markdown --wrap=none`.

### AST → HTML (exporter)

For SpecCompiler-built databases where `content_xhtml` is empty but `ast`
has data, the exporter converts AST → HTML via `pandoc -f json -t html`.

---

## File Splitting Strategy

The decompiler splits large specifications into multiple files:

- **Single file** (default): If total objects ≤ `threshold` (default 50)
  - Output: `{spec-slug}.md` containing the full specification

- **Multi-file**: If total objects > `threshold`
  - Root: `{spec-slug}.md` with `# SPEC_TYPE: Title` + include block
  - Children: `{spec-slug}/{section-slug}.md` per H2 section
  - Each child contains an H2 heading and all its nested descendants

Control via `--threshold`:
```bash
# Force multi-file even for small specs
python -m reqif.specir decompile --db db --output-dir out --threshold 1

# Force single file even for large specs
python -m reqif.specir decompile --db db --output-dir out --threshold 9999
```

---

## ID Stability and Round-Trips

The `IdMap` module (`id_map.py`) ensures stable ReqIF identifiers across
import/export cycles:

1. **On import**: Original ReqIF IDs are stored in the `id_map` table
   alongside SpecIR internal IDs
2. **On export**: If an ID mapping exists (from a previous import),
   the original ReqIF ID is reused
3. **For new objects**: Deterministic IDs are generated via SHA1 hash
   of the table name + SpecIR identifier

This means a ReqIF file imported and immediately re-exported will preserve
the original ReqIF identifiers, enabling interoperability with tools that
track objects by ID.

---

## Testing

Run the full test suite:

```bash
# Set PYTHONPATH to the vendor directory
export PYTHONPATH=dist/vendor/python

# All tests (131 tests)
python -m unittest discover \
    -s dist/vendor/python/reqif/specir/tests -p 'test_*.py' -v
```

Individual test files:

```bash
# Unit tests — schema, import, export, ID map, XHTML
python -m unittest reqif.specir.tests.test_specir -v

# Decompiler — model gen, decompiler, project gen, full round-trip
python -m unittest reqif.specir.tests.test_decompiler -v

# Content converter — AST/HTML → Markdown/HTML (requires pandoc)
python -m unittest reqif.specir.tests.test_content_converter -v

# Round-trip — ReqIF round-trips + CommonSpec output validation
python -m unittest reqif.specir.tests.test_round_trip -v

# CLI — end-to-end CLI integration via subprocess
python -m unittest reqif.specir.tests.test_cli -v

# Interop stress — StrictDoc↔ReqIF↔SpecIR↔CommonSpec pipelines (requires strictdoc)
python -m unittest reqif.specir.tests.test_interop_stress -v
```

### Test files

| File | Tests | Focus |
|------|-------|-------|
| `test_specir.py` | 18 | Schema, import, export, ID map, XHTML |
| `test_decompiler.py` | 20 | Model gen, decompiler, project gen |
| `test_content_converter.py` | 26 | Pandoc AST/HTML conversion |
| `test_round_trip.py` | 23 | ReqIF round-trips, CommonSpec attribute validation |
| `test_cli.py` | 4 | CLI subcommands end-to-end |
| `test_interop_stress.py` | 40 | StrictDoc↔ReqIF↔SpecIR↔CommonSpec interop, edit round-trips, double round-trip stability |

Tests use upstream ReqIF fixture files from
`dist/vendor/python/reqif/specir/tests/fixtures/`:
- `tc1000_simple_content.reqif` — 1 object, 8 attributes (all datatypes), 0 relations
- `tc1300_spec_relation.reqif` — 2 objects, 2 STRING attrs, 1 relation
- `interop/` — generated artifacts from stress tests (see Workflow 4 above)

Some tests require `pandoc` (bundled at `dist/bin/pandoc`).
These are skipped automatically when unavailable.
