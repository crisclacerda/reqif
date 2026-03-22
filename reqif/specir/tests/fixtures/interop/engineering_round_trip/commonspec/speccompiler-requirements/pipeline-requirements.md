## Pipeline Requirements @SRS-001-sec4

### SOFTWARE_FUNCTION: Pipeline Execution @SF-001

> description: Groups requirements for the core [TERM-15](#TERM-15) that drives document processing through [TERM-19](#TERM-19), [TERM-20](#TERM-20), [TERM-22](#TERM-22), [TERM-21](#TERM-21), [TERM-23](#TERM-23) phases with declarative handler dependencies.

> rationale: A structured processing pipeline enables separation of concerns, validation gates, and deterministic handler ordering.

Five-phase document processing lifecycle with [Handler](#TERM-16) orchestration and [Topological Sort](#TERM-25) ordering.

[TERM-15](@)

[TERM-19](@)

[TERM-20](@)

[TERM-22](@)

[TERM-21](@)

[TERM-23](@)

[TERM-16](@)

[TERM-25](@)

#### HIGH-LEVEL_REQUIREMENT: Five-Phase Lifecycle @HLR-PIPE-001

> description: Each phase serves a distinct purpose in document processing:

1.  **INITIALIZE**: Parse document AST and populate database with specifications, spec_objects, floats, relations, views, and attributes
2.  **ANALYZE**: Resolve relations between objects (link target resolution, type inference)
3.  **TRANSFORM**: Pre-compute views, render external content (PlantUML, charts), prepare for output
4.  **VERIFY**: Run proof views to validate data integrity, type constraints, cardinality rules
5.  **EMIT**: Assemble final documents and write to output formats (docx, html5, markdown, json)

> rationale: Separation of concerns enables validation between phases, allows early abort on errors, and supports format-agnostic processing until the final output stage.

> status: Approved

The pipeline shall execute handlers in a five-phase lifecycle: INITIALIZE, ANALYZE, TRANSFORM, VERIFY, EMIT.

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Handler Registration and Prerequisites @HLR-PIPE-002

> description: Handlers register via `register_handler(handler)` with required fields:

-   `name`: Unique string identifier for the handler
-   `prerequisites`: Array of handler names that must execute before this handler

Handlers declare participation in phases via hook methods (`on_initialize`, `on_analyze`, `on_verify`, `on_transform`, `on_emit`). Duplicate handler names cause registration error.

> rationale: Declarative prerequisites decouple handler ordering from registration order, enabling modular handler development and preventing implicit ordering dependencies.

> status: Approved

The pipeline shall support handler registration with declarative [Prerequisites](#TERM-24) for dependency ordering.

[TERM-24](@)

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Topological Ordering via Kahn’s Algorithm @HLR-PIPE-003

> description: For each phase, the pipeline:

1.  Identifies handlers participating in the phase (those with `on_{phase}` hooks)
2.  Builds dependency graph from prerequisites (only for participating handlers)
3.  Executes Kahn's algorithm to produce execution order
4.  Sorts alphabetically at each level for deterministic output
5.  Detects and reports circular dependencies with error listing remaining nodes

> rationale: Kahn's algorithm provides O(V+E) complexity, clear cycle detection, and deterministic ordering through alphabetic tie-breaking.

> status: Approved

The pipeline shall order handlers within each phase using topological sort with Kahn's algorithm.

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Phase Abort on VERIFY Errors @HLR-PIPE-004

> description: After running VERIFY phase, the pipeline checks diagnostics:has_errors(). If true, execution halts before EMIT phase, with TRANSFORM already completed. Error message is logged with error count. This prevents generating invalid output from documents with specification violations.

> rationale: Early abort on verification failures saves computation and prevents distribution of invalid specification documents. Errors in VERIFY indicate data integrity issues that would produce incorrect outputs.

> status: Approved

The pipeline shall abort execution after VERIFY phase if any errors are recorded.

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Batch Dispatch for All Phases @HLR-PIPE-005

> description: All handlers implement `on_{phase}(data, contexts, diagnostics)` hooks that receive the full contexts array. The pipeline orchestrator calls each handler's hook once per phase via `run_phase()`, passing all document contexts. Handlers are responsible for iterating over contexts internally.

This enables cross-document optimizations, transaction batching, and parallel processing within any phase.

> rationale: A uniform dispatch model simplifies the pipeline engine, eliminates the dual-path batch/per-doc dispatch, and allows handlers in any phase to optimize across all documents (e.g., wrapping DB operations in a single transaction, parallel output generation in EMIT).

> status: Approved

The pipeline shall use a single batch dispatch model for all phases where handlers receive all contexts at once.

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Context Creation and Propagation @HLR-PIPE-006

> description: The `execute(docs)` method creates context objects for each input document with:

-   `doc`: Pandoc document AST (via DocumentWalker)
-   `spec_id`: Specification identifier derived from filename
-   `config`: Preset configuration (styles, captions, validation)
-   `build_dir`: Output directory path
-   `output_format`: Target format (docx, html5, etc.)
-   `template`: Template name for model loading
-   `reference_doc`: Path to reference.docx for styling
-   `docx`, `html5`: Format-specific configuration
-   `outputs`: Array of {format, path} for multi-format output
-   `bibliography`, `csl`: Citation configuration
-   `project_root`: Root directory for resolving relative paths

Context flows through all phases, enriched by handlers (e.g., verification results in VERIFY phase).

> rationale: Unified context object provides handlers with consistent access to document metadata and build configuration without global state, enabling testable and isolated handler implementations.

> status: Approved

The pipeline shall create and propagate context objects containing document metadata and configuration through all phases.

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: CommonSpec Input Parsing @HLR-PIPE-007

> description: The INITIALIZE phase [TERM-16](#TERM-16)s parse the Pandoc [TERM-AST](#TERM-AST) and populate the six IR content tables according to these rules:

1.  **H1 headers** register as [SpecIR-01](#SpecIR-01) records with optional `TYPE:` prefix and `@PID` suffix
2.  **H2-H6 headers** register as [SpecIR-02](#SpecIR-02) records with type inference (explicit `TYPE:` prefix, implicit alias lookup, or default type fallback)
3.  **Blockquote lines** (`> key: value`) register as [SpecIR-04](#SpecIR-04) records attached to the enclosing spec object
4.  **Fenced code blocks** with `TypeRef:Label` class register as [SpecIR-03](#SpecIR-03) records
5.  **Markdown links** with `(@)` or `(#)` targets register as [SpecIR-05](#SpecIR-05) records
6.  **Inline code** with `TypeRef: content` syntax registers as [SpecIR-06](#SpecIR-06) records

Each handler populates its content table with content-addressable identifiers (SHA1) and preserves document ordering via `file_seq`.

> rationale: Formal parsing rules ensure deterministic lowering from CommonSpec to SpecIR, enabling round-trip fidelity and predictable behavior across document structures.

> status: Approved

The system shall parse [CommonSpec](#TERM-COMMONSPEC) documents during the [INITIALIZE Phase](#TERM-19) phase, lowering Markdown annotations into [Intermediate Representation](#TERM-IR) content tables.

[TERM-16](@)

[TERM-AST](@)

[SpecIR-01](@)

[SpecIR-02](@)

[SpecIR-04](@)

[SpecIR-03](@)

[SpecIR-05](@)

[SpecIR-06](@)

[TERM-COMMONSPEC](@)

[TERM-19](@)

[TERM-IR](@)

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Include File Expansion @HLR-PIPE-008

> description: Include expansion runs before the five-phase pipeline on each source document:

1.  Fenced code blocks with class `.include` are identified
2.  Each line in the block is treated as a relative file path
3.  Paths are resolved relative to the including file's directory
4.  Referenced files are read, parsed, and recursively expanded
5.  The include block is replaced with the parsed content blocks

Cycle detection prevents infinite recursion. Maximum include depth is bounded. Source position tracking attributes are injected for diagnostic reporting.

> rationale: Include expansion enables modular document authoring where specifications are composed from reusable fragments. Pre-pipeline expansion ensures all downstream handlers see a complete, flattened document.

> status: Approved

When a document contains `.include` code blocks, the system shall expand them by embedding the referenced file content before [Pipeline](#TERM-15) processing.

[TERM-15](@)

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: PID Auto-Generation @HLR-PIPE-009

> description: The PID generator runs in the ANALYZE phase before relation resolution:

1.  **Non-[TERM-COMPOSITE](#TERM-COMPOSITE) objects**: PIDs are generated using the type's `pid_prefix` and `pid_format` (e.g., `HLR-%03d` produces "HLR-001"), starting from the next available sequence number
2.  **[TERM-COMPOSITE](#TERM-COMPOSITE) objects**: Hierarchical PIDs are qualified by the specification PID (e.g., "SRS-sec1.2.3")

Auto-generated PIDs never overwrite explicit `@PID` annotations. Collision detection ensures global uniqueness across all specifications.

> rationale: Auto-generation reduces authoring burden while maintaining stable identifiers for traceability.

> status: Approved

When a spec object does not have an explicit `@PID`, the system shall auto-generate a [Project Identifier](#TERM-PID) during the [ANALYZE Phase](#TERM-20) phase based on the object's type definition.

[TERM-COMPOSITE](@)

[TERM-COMPOSITE](@)

[TERM-PID](@)

[TERM-20](@)

[SF-001](@)

#### HIGH-LEVEL_REQUIREMENT: Relation Type Inference @HLR-PIPE-010

> description: For each unresolved relation, the relation analyzer:

1.  **Filter**: Identifies candidate relation types whose constraints are compatible with the relation's [TERM-SELECTOR](#TERM-SELECTOR), source attribute, source type, and target type
2.  **Resolve**: Calls the resolver (determined by the type's extends chain root) to find the target object
3.  **Score**: Counts matching non-NULL constraints across all four dimensions; NULL constraints act as wildcards (match anything but do not increase specificity)
4.  **Pick**: The highest specificity match wins; ties mark the relation as ambiguous

Same-specification targets are preferred over cross-specification targets. The relation's `target_ref` and `type_ref` are updated in the database.

> rationale: Type inference from constraints eliminates explicit relation type annotation in source documents, reducing authoring burden. Specificity scoring ensures the most specific matching type is selected, enabling both generic and specialized relation types to coexist.

> status: Approved

The system shall infer relation types during the [ANALYZE Phase](#TERM-20) phase using constraint-based matching with [Specificity Scoring](#TERM-SPECIFICITY) scoring.

[TERM-SELECTOR](@)

[TERM-20](@)

[TERM-SPECIFICITY](@)

[SF-001](@)
