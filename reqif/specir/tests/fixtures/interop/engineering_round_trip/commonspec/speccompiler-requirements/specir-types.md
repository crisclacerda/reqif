## SpecIR Types @SRS-001-sec2

SpecIR (see [SpecIR](#TERM-SPECIR)) is the data model that SpecCompiler builds from source Markdown during the [INITIALIZE Phase](#TERM-19) phase. The core task of parsing is to *lower* Markdown annotations into a set of typed content tables that the [Pipeline](#TERM-15) can analyze, transform, verify, and emit. The entries below define each of these six content tables as a formal tuple specifying the Markdown syntax that produces it.

[TERM-SPECIR](@)

[TERM-19](@)

[TERM-15](@)

### DICTIONARY_ENTRY: Specification @SpecIR-01

> description: **Formal definition:** `$: S = (tau, n, "pid", cc A, cc O)` --- a tuple of type, title, project identifier, attributes, and child objects.

**Syntax:** `# [TypeRef:] Text [@PID]`

**Full specification:** See the CommonSpec Language Specification for the complete grammar, type inference rules, and examples.

A **Specification** is the root document container created from an H1 header. It represents a complete document like an SRS, SDD, or SVC. Each specification has a type, optional PID, and contains attributes and all spec objects within that document.

### DICTIONARY_ENTRY: Spec Object @SpecIR-02

> description: **Formal definition:** `$: O = (tau, "title", "pid", beta, cc A, cc F, cc R, cc V, cc O)` --- a tuple of type, title, project identifier, body content, attributes, floats, relations, views, and child objects.

**Syntax:** `##...###### [TypeRef:] Title [@PID]`

**Full specification:** See the CommonSpec Language Specification for the complete grammar, type inference, PID auto-generation, and examples.

A **Spec Object** represents a traceable element in a specification document, created from H2-H6 headers. Objects can be requirements (HLR, LLR), verification cases (VC), design elements (FD, CSC, CSU), or structural sections (SECTION). Each object has a type, PID and can contain attributes, body content, floats, relations, views, and child objects.

### DICTIONARY_ENTRY: Spec Float @SpecIR-03

> description: **Formal definition:** `$: F = (tau, "label", cc "kv", "content")` --- a tuple of type, label, key-value metadata, and raw content.

**Syntax:** ```` ```TypeRef:Label[{Key=Value, ...}] Content ``` ````

**Full specification:** See the CommonSpec Language Specification for float types, aliases, counter groups, and examples.

A **Spec Float** represents a floating element like a figure, table, or diagram. Floats are created from fenced code blocks with a `TypeRef:Label` pattern. They are automatically numbered within their counter group and can be cross-referenced by their label. Some floats require external rendering (e.g., PlantUML diagrams).

### DICTIONARY_ENTRY: Attribute @SpecIR-04

> description: **Formal definition:** `$: A = (tau, beta, cc R)` --- a triple of attribute type, blockquote content, and child relations.

**Syntax:** `> TypeRef: value`

**Datatypes:** STRING, INTEGER, REAL, BOOLEAN, DATE, ENUM, XHTML.

**Full specification:** See the CommonSpec Language Specification for the complete datatype semantics, attribute constraints, and examples.

An **Attribute** stores metadata for specifications and spec objects using an Entity-Attribute-Value (EAV) pattern. Attributes are defined in blockquotes following headers and support multiple datatypes including strings, integers, dates, enums, and rich XHTML content (Pandoc AST). Relations are extracted from the AST. Attribute definitions constrain which attributes each object type can have.

### DICTIONARY_ENTRY: Spec Relation @SpecIR-05

> description: **Formal definition:** `$: R = (s, t, sigma, alpha)` --- a 4-tuple of source object, target element, link selector, and source attribute.

**Type inference:** `$: rho = "infer"(sigma, alpha, tau_s, tau_t)` --- the relation type is inferred by constraint matching with most-specific-wins across selector, attribute, source type, and target type.

**Syntax:** `[Target](selector)` where the URL starts with `@` or `#`. Selectors are not hardcoded --- they are defined by relation types in the model (e.g., `PID_REF` defines `@`, `LABEL_REF` defines `#`, `XREF_CITATION` defines `@cite,@citep`). Models can register any `@...` or `#...` selector.

**Full specification:** See the CommonSpec Language Specification for the complete inference algorithm and examples.

A **Spec Relation** represents a traceability link between specification elements. Relations are created from Markdown links where the link target (URL) acts as a **selector** that drives type inference. The relation type is not authored explicitly --- it is inferred by constraint matching: each relation type defines optional constraints on selector, source attribute, source type, and target type. The most specific match (most non-NULL constraints) wins.

### DICTIONARY_ENTRY: Spec View @SpecIR-06

> description: **Formal definition:** `$: V = (tau, omega)` --- a pair of view type and parameter string.

**Syntax:** `` `TypeRef:[ViewParam]` ``

**Full specification:** See the CommonSpec Language Specification for view types, materialization strategies, and examples.

A **Spec View** represents a dynamic query or generated content block. Views are materialized during the TRANSFORM phase and can generate tables of contents (TOC), lists of figures (LOF), or custom queries, abbreviations, and inline math. Views enable dynamic document assembly based on specification data.
