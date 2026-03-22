## System Concepts @SRS-001-sec10

### DICTIONARY_ENTRY: CommonSpec @TERM-COMMONSPEC

> description: **Purpose:** Defines the input language for SpecCompiler. Extends standard Markdown (CommonMark) with six constructs: specifications, spec objects, spec floats, attributes, spec relations, and spec views.

**Architecture:** CommonSpec (language) compiles into SpecIR (intermediate representation) via SpecCompiler (compiler).

**Specification:** See the CommonSpec Language Specification (`docs/commonspec/`) for the formal definition.

> domain: Core

> term: CommonSpec

A **structured Markdown language** for authoring typed, traceable specifications.

### DICTIONARY_ENTRY: SpecIR @TERM-SPECIR

> acronym: SpecIR

> description: **Purpose:** Provides a portable, queryable storage format for specification data. Compilation target for CommonSpec and interchange format for other tools (ReqIF, DOORS CSV, SQL).

**Schema:** Two core layers: Type System tables (metamodel) and Content tables (data). Build infrastructure and FTS tables are not part of the SpecIR standard.

**Specification:** See the SpecIR Schema Specification (`docs/specir/`) for the formal definition.

> domain: Core

> term: Specification Intermediate Representation

A **typed relational intermediate representation** for specifications, stored in SQLite.

### DICTIONARY_ENTRY: ANALYZE Phase @TERM-20

> description: **Purpose:** Resolves cross-references between spec objects and infers missing type information.

**Position:** Second phase after INITIALIZE, before TRANSFORM.

The **second phase** in the pipeline that resolves references and infers types.

### DICTIONARY_ENTRY: Build Cache @TERM-30

> description: **Purpose:** Stores content hashes to detect which documents have changed since last build.

**Implementation:** Compares current file hash against cached hash to skip unchanged files.

**SHA1 hashes** for detecting document changes.

### DICTIONARY_ENTRY: Counter Group @TERM-28

> description: **Purpose:** Groups related float types to share sequential numbering.

**Example:** FIG and DIAGRAM types may share a counter, producing Figure 1, Figure 2, etc.

**Float types** sharing a numbering sequence.

### DICTIONARY_ENTRY: CSC (Computer Software Component) @TERM-36

> description: **Purpose:** Groups software units into higher-level structural components for design allocation.

**Examples:** `src/core`, `src/db`, `src/infra`.

A **MIL-STD-498 architectural decomposition element** representing a subsystem, layer, package, or service.

### DICTIONARY_ENTRY: CSU (Computer Software Unit) @TERM-37

> description: **Purpose:** Captures file-level implementation units allocated to functional descriptions.

**Examples:** `src/core/pipeline.lua`, `src/db/manager.lua`.

A **MIL-STD-498 implementation decomposition element** representing a source file or code unit.

### DICTIONARY_ENTRY: Data View @TERM-35

> description: **Purpose:** Produces structured data that can be injected into chart floats.

**Implementation:** Lua scripts that query database and return chart-compatible data structures.

A **Lua module** generating data for chart injection.

### DICTIONARY_ENTRY: EAV Model @TERM-EAV

> description: **Purpose:** Flexible schema for storing typed attributes on spec objects.

**Structure:** Entity (spec object), Attribute (key name), Value (typed content).

**Entity-Attribute-Value** pattern for typed attribute storage.

### DICTIONARY_ENTRY: EMIT Phase @TERM-23

> description: **Purpose:** Assembles transformed content and writes final output documents.

**Position:** Final phase after VERIFY.

The **final phase** in the pipeline that assembles and outputs documents.

### DICTIONARY_ENTRY: Float @TERM-04

A **numbered element** (table, figure, diagram) with caption and cross-reference. See [Spec Float](#SpecIR-03) for full definition.

[SpecIR-03](@)

### DICTIONARY_ENTRY: External Renderer @TERM-34

> description: **Purpose:** Delegates rendering to external tools via subprocess execution.

**Examples:** PlantUML JAR for diagrams, chart libraries for data visualization.

**Subprocess-based rendering** for types like PLANTUML, CHART.

### DICTIONARY_ENTRY: Handler @TERM-16

> description: **Purpose:** Encapsulates processing logic for a content type across all pipeline phases.

**Structure:** Implements phase methods (initialize, analyze, verify, transform, emit) for its content type.

A **modular component** that processes specific content types through pipeline phases.

### DICTIONARY_ENTRY: INITIALIZE Phase @TERM-19

> description: **Purpose:** Parses markdown AST and populates intermediate representation containers.

**Position:** First phase, entry point for document processing.

The **first phase** in the pipeline that parses AST and populates IR containers.

### DICTIONARY_ENTRY: Model @TERM-33

> description: **Purpose:** Bundles related type definitions, handlers, and styling for specific documentation domains.

**Examples:** SRS model for software requirements, HRS model for hardware requirements.

A **collection of type definitions**, handlers, and styles for a domain.

### DICTIONARY_ENTRY: Output Cache @TERM-31

> description: **Purpose:** Tracks when outputs were last generated to enable incremental builds.

**Implementation:** Compares source modification time against cached output timestamp.

**Timestamps** for incremental output generation.

### DICTIONARY_ENTRY: Phase @TERM-17

> description: **Purpose:** Separates document processing into well-defined sequential stages.

**Phases:** INITIALIZE, ANALYZE, TRANSFORM, VERIFY, EMIT.

A **distinct stage** in document processing with specific responsibilities.

### DICTIONARY_ENTRY: Pipeline @TERM-15

> description: **Purpose:** Orchestrates document processing through sequential phases.

**Flow:** Each phase completes for all handlers before the next phase begins.

The **5-phase processing system** (INITIALIZE -\> ANALYZE -\> TRANSFORM -\> VERIFY -\> EMIT).

### DICTIONARY_ENTRY: Prerequisites @TERM-24

> description: **Purpose:** Declares which handlers must complete before a given handler can execute.

**Usage:** Handlers declare prerequisites to ensure data dependencies are satisfied.

**Handler dependencies** that determine execution order.

### DICTIONARY_ENTRY: Topological Sort @TERM-25

> description: **Purpose:** Determines valid execution order for handlers based on dependencies.

**Algorithm:** Uses Kahn's algorithm to produce a topologically sorted handler sequence.

**Kahn's algorithm** for ordering handlers by prerequisites.

### DICTIONARY_ENTRY: TRANSFORM Phase @TERM-22

> description: **Purpose:** Materializes database views into content and applies content transformations.

**Position:** Third phase after ANALYZE, before VERIFY.

The **third phase** in the pipeline that materializes views and rewrites content.

### DICTIONARY_ENTRY: Type Alias @TERM-27

> description: **Purpose:** Provides shorthand or alternative names for types.

**Example:** `csv` is an alias for the TABLE type in float definitions.

**Alternative syntax identifier** for a type (e.g., "csv" -\> "TABLE").

### DICTIONARY_ENTRY: Type Loader @TERM-38

> description: **Purpose:** Dynamically discovers and instantiates type handlers from model definitions.

**Implementation:** Scans model directories for handler definitions and registers them.

**System that discovers and loads** type handlers from model directories.

### DICTIONARY_ENTRY: Type Registry @TERM-26

> description: **Purpose:** Stores type definitions including attributes, aliases, and validation rules.

**Tables:** spec_object_types, spec_float_types, spec_attribute_types, etc.

**Database tables** (spec\_\*\_types) storing type definitions.

### DICTIONARY_ENTRY: VERIFY Phase @TERM-21

> description: **Purpose:** Validates document content using proof views and constraint checking.

**Position:** Fourth phase after TRANSFORM, before EMIT.

The **fourth phase** in the pipeline that validates content via proof views.

### DICTIONARY_ENTRY: Abstract Syntax Tree @TERM-AST

> acronym: AST

> description: **Purpose:** Represents document structure as a hierarchical tree of elements.

**Source:** Pandoc parses Markdown and produces JSON AST.

**Usage:** Handlers walk the AST to extract spec objects, floats, and relations.

> domain: Core

> term: Abstract Syntax Tree

The **tree representation** of document structure produced by Pandoc.

### DICTIONARY_ENTRY: Full-Text Search @TERM-FTS

> acronym: FTS

> description: **Purpose:** Indexes specification text for fast full-text search queries.

**Implementation:** SQLite FTS5 virtual tables populated during EMIT phase.

**Usage:** Web application uses FTS for search functionality.

> domain: Database

> term: Full-Text Search

**FTS5 virtual tables** enabling search across specification content.

### DICTIONARY_ENTRY: High-Level Requirement @TERM-HLR

> acronym: HLR

> description: **Purpose:** Defines system-level requirements that guide design and implementation.

**Traceability:** HLRs trace to verification cases (VC) and are realized by functional descriptions (FD).

> domain: Core

> term: High-Level Requirement

A **top-level functional or non-functional requirement** that captures what the system must do or satisfy.

### DICTIONARY_ENTRY: Intermediate Representation @TERM-IR

> acronym: IR

> description: **Purpose:** Stores parsed specification content in queryable form.

**Storage:** SQLite database with spec_objects, spec_floats, spec_relations tables.

**Lifecycle:** Populated during INITIALIZE, queried and modified through remaining phases.

> domain: Core

> term: Intermediate Representation

The **database-backed representation** of parsed document content.

### DICTIONARY_ENTRY: Project Identifier @TERM-PID

> acronym: PID

> description: **Purpose:** Provides unique, human-readable identifiers for traceability and cross-referencing.

**Syntax:** Written as `@PID` in header text (e.g., `## HLR: Requirement Title @REQ-001`).

**Auto-generation:** PIDs can be auto-generated from type prefix and sequence number.

> domain: Core

> term: Project Identifier

A **unique identifier** assigned to spec objects for cross-referencing (e.g., `@REQ-001`).

### DICTIONARY_ENTRY: Proof View @TERM-PROOF

> acronym: -

> description: **Purpose:** Defines validation rules as SQL queries that detect specification errors.

**Execution:** Run during the VERIFY phase; violations are reported as diagnostics.

**Examples:** Missing required attributes, unresolved relations, cardinality violations.

> domain: Core

> term: Proof View

A **SQL query** that validates data integrity constraints during the VERIFY phase.

### DICTIONARY_ENTRY: SQLite Database @TERM-SQLITE

> acronym: -

> description: **Purpose:** Provides persistent, portable storage for the intermediate representation.

**Benefits:** Single-file storage, ACID transactions, SQL query capability.

**Usage:** All pipeline phases read/write to SQLite via the database manager.

> domain: Database

> term: SQLite Database

The **embedded database engine** storing the IR and build cache.

### DICTIONARY_ENTRY: Traceable Object @TERM-TRACEABLE

> acronym: -

> description: **Purpose:** Base type for objects that can be linked via traceability relations.

**Types:** Any spec object type registered in the model (e.g., HLR, LLR, SECTION).

**Relations:** Model-defined relation types (e.g., XREF_FIGURE, XREF_CITATION) inferred by specificity matching.

> domain: Core

> term: Traceable Object

A **specification object** that participates in traceability relationships.

### DICTIONARY_ENTRY: Type @TERM-TYPE

> acronym: -

> description: **Purpose:** Defines the schema, validation rules, and rendering behavior for a category of elements.

**Categories:** Object types (HLR, SECTION), float types (FIGURE, TABLE), relation types (TRACES_TO), view types (TOC, LOF).

**Registration:** Types are loaded from model directories and stored in the type registry.

> domain: Core

> term: Type

A **category definition** that governs behavior for objects, floats, relations, or views.

### DICTIONARY_ENTRY: Verification Case @TERM-VC

> acronym: VC

> description: **Purpose:** Defines how requirements are verified through test procedures and expected results.

**Traceability:** VCs trace to HLRs via `traceability` attribute links.

**Naming:** VC PIDs follow the pattern `VC-{category}-{seq}` (e.g., `VC-PIPE-001`).

> domain: Core

> term: Verification Case

A **test specification** that verifies a requirement or set of requirements.

### DICTIONARY_ENTRY: Composite Object Type @TERM-COMPOSITE

> description: **Purpose:** Distinguishes object types that represent document structure (e.g., SECTION) from traceable types that receive standalone PIDs (e.g., HLR, VC).

**PID behavior:** Composite objects get hierarchical PIDs derived from the specification PID (e.g., `SRS-sec1.2.3`). Non-composite objects get independent PIDs from their `pid_prefix` and `pid_format` (e.g., `HLR-001`).

**Configuration:** Set via `is_composite = true` in the type definition module.

> domain: Core

> term: Composite Object Type

A **spec object type** whose instances receive hierarchical PIDs qualified by the parent specification PID.

### DICTIONARY_ENTRY: Relation Selector @TERM-SELECTOR

> description: **Purpose:** Identifies what kind of relation a Markdown link represents, enabling type-driven inference.

**Selectors:** `@` (PID reference, e.g., `[HLR-001](@)`), `#` (label reference, e.g., `[fig:diagram](#)`), `@cite` (bibliographic citation).

**Configuration:** Each relation type declares a `link_selector` value in `spec_relation_types`. Selectors are model-defined, not hardcoded.

> domain: Core

> term: Relation Selector

The **URL scheme portion** of a Markdown link that drives relation type inference.

### DICTIONARY_ENTRY: Specificity Scoring @TERM-SPECIFICITY

> description: **Purpose:** Resolves ambiguity when multiple relation types match a given link by selecting the most specific type.

**Algorithm:** Each non-NULL constraint match across four dimensions (selector, source_attribute, source_type, target_type) adds one point. The highest total score wins. Ties mark the relation as ambiguous.

**Example:** A relation type with constraints on selector + source_type + target_type (score 3) wins over one with only selector (score 1).

> domain: Core

> term: Specificity Scoring

The **constraint-matching score** used to select the best relation type during type inference.

### DICTIONARY_ENTRY: Processed Intermediate Representation @TERM-PIR

> acronym: P-IR

> description: **Purpose:** Provides a single hash that represents the fully processed state of a specification, including all resolved relations, materialized views, and transformed content.

**Usage:** The output cache stores the P-IR hash alongside each generated output file. When rebuilding, the system compares the current P-IR hash to the cached hash to determine if output regeneration is needed.

**Distinction:** Unlike the build cache (which tracks source file hashes), the P-IR hash captures the post-processing state, detecting changes from cross-document operations.

> domain: Core

> term: Processed Intermediate Representation

The **complete specification state** after all pipeline phases have executed, captured as a hash for output cache invalidation.

### DICTIONARY_ENTRY: Newline-Delimited JSON @TERM-NDJSON

> acronym: NDJSON

> description: **Purpose:** Provides machine-parseable structured logging suitable for CI/CD log aggregation and filtering with tools like `jq`.

**Format:** One JSON object per line with fields: `level`, `message`, `timestamp`, and optional context fields.

**Usage:** The logger emits NDJSON when output is not connected to a TTY (e.g., piped to a file or running in CI).

> domain: Infrastructure

> term: Newline-Delimited JSON

A **text format** where each line is a valid JSON object, used for structured log output.

### DICTIONARY_ENTRY: Proof Policy @TERM-PROOFPOLICY

> description: **Purpose:** Allows projects to control validation strictness by mapping each proof view to a severity level.

**Severity levels:** `error` (blocks output generation), `warn` (reported but build continues), `ignore` (suppressed).

**Configuration:** Set in the `validation:` section of `project.yaml` (e.g., `traceability_hlr_to_vc: warn`).

**Default:** When a policy_key is not configured, the system applies its built-in default severity.

> domain: Core

> term: Proof Policy

A **configuration mapping** from proof view `policy_key` to severity level, controlling which violations are reported and at what severity.

### DICTIONARY_ENTRY: Diagnostic Record @TERM-DIAGNOSTIC

> description: **Purpose:** Provides machine-parseable and human-readable feedback on specification errors and warnings throughout all pipeline phases.

**Fields:** Each record contains `file` (source path), `line` (source line number), `code` (domain-prefixed identifier, e.g., `SD-301`), and `msg` (human-readable description).

**Severity:** Errors trigger abort after [TERM-21](#TERM-21) phase; warnings are reported but do not block output generation.

> domain: Core

> term: Diagnostic Record

A **structured error or warning record** emitted by [TERM-16](#TERM-16)s during [TERM-15](#TERM-15) processing.

[TERM-21](@)

[TERM-16](@)

[TERM-15](@)

### DICTIONARY_ENTRY: Build Graph @TERM-BUILDGRAPH

> description: **Purpose:** Tracks which files are included by each root document, enabling change detection across include hierarchies.

**Storage:** Stored in the `build_graph` table with columns `root_path` (the including document), `node_path` (the included file), and `node_sha1` (content hash at build time).

**Usage:** Queried by [TERM-30](#TERM-30) `is_document_dirty_with_includes()` to determine if any included file has changed since the last successful build.

> domain: Database

> term: Build Graph

A **dependency tracking structure** recording include file hierarchies for incremental rebuild support.

[TERM-30](@)

### DICTIONARY_ENTRY: Placeholder Block @TERM-PLACEHOLDERBLOCK

> description: **Purpose:** Marks positions in the assembled Pandoc document where floats and views will be substituted during the [TERM-23](#TERM-23) phase.

**Mechanism:** During assembly, [CSU-034](sdd.ext#CSU-034) inserts CodeBlock elements at the correct `file_seq` positions. Downstream handlers ([CSU-035](sdd.ext#CSU-035) for floats, [CSU-036](sdd.ext#CSU-036) for views) match these placeholders by label and replace them with rendered content.

**Lifecycle:** Created during assembly, consumed during float/view emission, never present in final output.

> domain: Pipeline

> term: Placeholder Block

A **CodeBlock marker** inserted during document assembly for deferred [SpecIR-03](#SpecIR-03) and [SpecIR-06](#SpecIR-06) resolution.

[TERM-23](@)

[SpecIR-03](@)

[SpecIR-06](@)
