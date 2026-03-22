## Storage Requirements @SRS-001-sec5

### SOFTWARE_FUNCTION: Specification Persistence @SF-002

> description: Groups requirements for the persistence layer including ACID-compliant storage, [TERM-EAV](#TERM-EAV) attribute model, [TERM-30](#TERM-30), [TERM-31](#TERM-31), and incremental rebuild support.

> rationale: Reliable persistence with change detection enables efficient rebuilds for large specification projects.

[SQLite Database](#TERM-SQLITE)-based storage with incremental build support and output caching.

[TERM-EAV](@)

[TERM-30](@)

[TERM-31](@)

[TERM-SQLITE](@)

#### HIGH-LEVEL_REQUIREMENT: SQLite Persistence @HLR-STOR-001

> description: All specifications, spec_objects, floats, relations, views, and attribute values stored in SQLite database. Database operations wrapped in transactions to ensure atomicity, consistency, isolation, and durability.

> rationale: SQLite provides a reliable, single-file persistence layer suitable for specification documents. ACID guarantees prevent data corruption during concurrent access or system failures.

> status: Approved

The system shall persist all specification data to SQLite database with ACID guarantees.

[SF-002](@)

#### HIGH-LEVEL_REQUIREMENT: EAV Attribute Model @HLR-STOR-002

> description: Attribute values stored in attribute_values table with polymorphic typed columns (string_value, int_value, real_value, bool_value, date_value, enum_ref). Each attribute record links to owner object via owner_ref and stores datatype for proper retrieval.

> rationale: EAV pattern enables flexible attribute schemas without database migrations. Different spec object types (HLR, LLR, VC) have different attributes that can evolve independently.

> status: Approved

The system shall store spec object attributes using Entity-Attribute-Value pattern.

[SF-002](@)

#### HIGH-LEVEL_REQUIREMENT: Build Cache @HLR-STOR-003

> description: Source file hashes stored in source_files table (path, sha1). Build cache module provides is_document_dirty() to check if document content has changed since last build. Hash comparison enables change detection.

> rationale: Hash-based change detection allows the build system to skip unchanged documents, reducing rebuild times for large specification sets.

> status: Approved

The system shall maintain a build cache for document hash tracking.

[SF-002](@)

#### HIGH-LEVEL_REQUIREMENT: Output Cache @HLR-STOR-004

> description: Output cache stored in output_cache table (spec_id, output_path, pir_hash, generated_at). P-IR (Processed Intermediate Representation) hash captures complete specification state. is_output_current() checks if output file exists and P-IR hash matches cached value.

> rationale: Output caching avoids regenerating unchanged outputs (docx, html5). P-IR hash ensures output is regenerated when any upstream data changes, not just source file changes.

> status: Approved

The system shall cache output generation state with P-IR hash and timestamps.

[SF-002](@)

#### HIGH-LEVEL_REQUIREMENT: EAV Pivot Views for External Queries @HLR-STOR-006

> description: For each non-composite spec_object_type, a view named view\_{type_lower}\_objects is dynamically generated (e.g., view_hlr_objects, view_vc_objects). Each view flattens the EAV join into one row per object with typed attribute columns, enabling queries like SELECT \* FROM view_hlr_objects WHERE status = \'approved\'. These views are NOT used by internal pipeline queries --- all internal code queries the raw EAV tables directly because it needs access to raw_value, datatype, ast, enum_ref, and other columns that the pivot views abstract away. Internal queries also frequently operate cross-type or need COUNT/EXISTS checks that the MAX()-based pivot cannot provide.

> rationale: External BI tools, ad-hoc SQL queries, and custom model scripts benefit from a flat relational interface over the EAV model. Generating views at runtime from the type system ensures the columns always match the current model configuration without manual maintenance.

> status: Approved

The system shall generate per-object-type SQL views that pivot the EAV attribute model into typed columns for external BI queries.

[SF-002](@)

#### HIGH-LEVEL_REQUIREMENT: Incremental Rebuild Support @HLR-STOR-005

> description: Build graph stored in build_graph table (root_path, node_path, node_sha1). Tracks include file dependencies for each root document. is_document_dirty_with_includes() checks root document and all includes. update_build_graph() refreshes dependency tree after successful build.

> rationale: Specification documents often include sub-files. Incremental builds must detect changes in any included file to trigger rebuild of parent document. Build graph captures this dependency structure.

> status: Approved

The system shall support incremental rebuilds via build graph tracking.

[SF-002](@)
