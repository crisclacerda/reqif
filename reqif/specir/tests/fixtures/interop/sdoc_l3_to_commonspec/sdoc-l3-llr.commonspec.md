# SDOC_SPECIFICATION_TYPE_SINGLETON: StrictDoc Low-Level Requirements Specification (L3)

## TEXT: TEXT-70267357-01e6-4bec-8563-2b862be4f849 @TEXT-001

The level 3 low-level requirements specification of StrictDoc (L3/LLR) is derived from StrictDoc\'s L2 high-level (L2/HLR) requirements specification. The purpose of L3/LLR is to provide the lowest-level requirements from which StrictDoc\'s source code can be directly implemented without further information.

It is at the L3 level that the StrictDoc requirements are specified for the actual software implementers, including both the StrictDoc developers and AI agents such as Codex. At the same time, the L2/HLR requirements provide the framework for the WHAT and WHY of the implementation instructions that are specified by this L3/LLR.

NOTE: This specification level is under construction. Many L2/HLR requirements will be gradually moved to be here at the L3/HLR level.

## Markdown text markup @SEC-001

### REQUIREMENT: Read Markdown markup @SDOC-LLR-183

> STATUS: Active

StrictDoc shall support reading Markdown files into in-memory SDoc documents.

### REQUIREMENT: Write Markdown markup @SDOC-LLR-197

> STATUS: Active

StrictDoc shall support writing in-memory SDoc documents to Markdown files.

### REQUIREMENT: Markdown files discovery @SDOC-LLR-192

> STATUS: Active

StrictDoc shall discover Markdown files `*.md` and `*.markdown` using the same mechanism as used for SDoc files.

### REQUIREMENT: Identical Markdown content by import/export roundtrip @SDOC-LLR-196

> STATUS: Active

> RATIONALE: A consistent import/export roundtrip implementation and testing reduces the risk of the Markdown bi-directional import/export corruption.

StrictDoc shall ensure that identical Markdown content is produced every time StrictDoc reads a Markdown file and then writes it to another Markdown file.

The following aspects shall additionally apply:

-   For MVP, line-endings should support both LF (Linux/macOS-style) and CRLF (Windows-style).
-   The `export --formats=markdown` shall work for any format readable by StrictDoc, including Markdown itself, SDoc, RDF (future growth), ReqIF, etc.

NOTE: The write-back to Markdown file must happen through proper AST serialization, not just by giving back the original read Markdown source.

Exceptions:

Edge cases related to handling non-default input formats are postponed after the Markdown MVP is implemented. For example:

-   Markdown reader encounters content format #3 (implicit field) via \[LINK: SDOC-LLR-185\], but writer always emits #1/#2 for content via \[LINK: SDOC-LLR-198\]. In this case the content will not be identical, but it is accepted for an MVP implementation.

### REQUIREMENT: Markdown formats @SDOC-LLR-191

> STATUS: Active

> RATIONALE: CommonMark core is the most portable target across parsers.

StrictDoc shall rely only on CommonMark core syntax v0.31.2 for SDoc node recognition.

### REQUIREMENT: Meta fields vs content fields @SDOC-LLR-186

> STATUS: Active

StrictDoc shall recognize the following Markdown nodes as SDoc nodes:

``` markdown
### Node title
(empty line)
**Meta field name 1**:
**Meta field name 2**:
...
(empty line)
**Note content field 1**: ...
(empty line)
**Note content field 2**: ...
...
```

An SDoc node terminates when another Markdown section header or an EOF is encountered.

NOTE: There are no limitations to node level. A Markdown node can be at level 2, 3, etc. The level 1 is served for a root document node (document title with optional fields).

### REQUIREMENT: One Markdown file \u2014 One SDoc document @SDOC-LLR-189

> STATUS: Active

StrictDoc shall parse Markdown files using the \"one Markdown file u2014 one SDoc document\" principle.

### REQUIREMENT: Strict ban for redundant empty lines @SDOC-LLR-195

> STATUS: Active

When a parsing Markdown file, if StrictDoc encounters two or more consecutive empty lines and the lines are not within a Markdown code block or a Markdown blockquote block, StrictDoc shall raise a StrictDocSemanticError.

NOTE: Empty lines includes whitespace-only lines which StrictDoc shall ban as well.

### REQUIREMENT: Syntax for meta and content field names @SDOC-LLR-194

> STATUS: Active

StrictDoc shall recognize the meta and content field names according to the following rules:

-   Format is: `**Field name**:`.
-   Alphanumeric character range, separated by spaces, underscores or dashes.

Examples:

-   `**Statement**:`
-   `**STATEMENT**:`
-   `**IMPORTANT_STATEMENT**:`
-   `**SPDX-Req-ID**:`

### REQUIREMENT: Three conventions for meta fields @SDOC-LLR-184

> STATUS: Active

StrictDoc shall support reading out SDoc nodes out of Markdown sections arranged in the following way: 1) Requirements with meta-information stored in bullet point list: .. code-block:: markdown \### Requirement title - \*\*MID\*\*: abcdabcdabcdabcdabcdabcdabcdabcdabcd - \*\*UID\*\*: REQ-001 - \*\*Status\*\*: Draft System A shall do B. When a Markdown title is followed by a full empty line followed by a bullet list and the bullet list follows the format \`\`- \*\*\*\*: \`\`, the bullet list must be treated as a list of meta fields. The bullet list is terminated by one empty line. 2) Requirements with meta-information stored in consecutive lines separated by the \"\\\\\\\\\" character: .. code-block:: markdown \### Requirement title \*\*MID\*\*: abcdabcdabcdabcdabcdabcdabcdabcdabcd \\\\ \*\*UID\*\*: REQ-001 \\\\ \*\*Status\*\*: Draft System A shall do B. When a Markdown title is followed by a full empty line followed by list of lines in the format \`\`\*\*\*\*: \\\\\`\`, the list must be treated as a list of meta fields. The line list is terminated by one empty line. The last line shall not end with a \"\\\\\" character. 3) Requirements with meta-information stored in consecutive lines separated by the two empty space characters (as officially supported by Markdown): .. code-block:: markdown \### Requirement title \*\*MID\*\*: abcdabcdabcdabcdabcdabcdabcdabcdabcd \*\*UID\*\*: REQ-001 \*\*Status\*\*: Draft System A shall do B. When a Markdown title is followed by a full empty line followed by list of lines in the format \`\`\*\*\*\*: \`\`, the list must be treated as a list of meta fields. The list is terminated by one empty line. Each given node must follow only one of these three syntaxes. If StrictDoc encounters that a single node has more one or more fields of a mixed style, it must give up parsing this node as a valid node, and treat it as a non-normative SECTION/TEXT node. As of Markdown MVP, the default and preferred syntax: shall be #2 with backslashes.

### REQUIREMENT: Valid formats for multi-line fields @SDOC-LLR-185

> STATUS: Active

StrictDoc shall recognize SDoc node multiline fields from the following three formats

1)  Explicit field name:

``` markdown
### Requirement title

- **MID**: abcdabcdabcdabcdabcdabcdabcdabcdabcd

 **Statement**: System A shall do B.
```

2)  Explicit field name with a line break:

``` markdown
### Requirement title

- **MID**: abcdabcdabcdabcdabcdabcdabcdabcdabcd

 **Statement**:

 System A shall do B.
```

3)  Implicit field name with a line break:

``` markdown
### Requirement title

**MID**: abcdabcdabcdabcdabcdabcdabcdabcdabcd

System A shall do B.

**Rationale**: This requirement is important because XYZ.
```

In this case, StrictDoc shall recognize the `System A shall do B.` as if it was written as `**Statement**: System A shall do B.` and recognize the rationale part as an explicitly written multiline field.

As of Markdown MVP, the default and preferred syntax shall be:

-   #1 for values with single-line or single-paragraph/block strings.
-   #2 for values with multiple markdown blocks separated by full empty lines.

### REQUIREMENT: Support node parent relations @SDOC-LLR-202

> STATUS: Active

StrictDoc shall support node relations in Markdown using the meta field: .. code-block:: markdown \*\*Relations\*\*: , , \... When reading Markdown: - Each UID from the Relations field shall be converted to a relation with TYPE: Parent and VALUE: . - All extra spaces shall be normalized before parsing to canonical \`\`, , \...\`\`. - The Markdown reader shall not check whether any UID actually exists. This task is deferred to the traceability index builder. When writing Markdown, SDoc node relations with TYPE: Parent and no ROLE shall be serialized back to the same Relations field as a comma-separated UID list. NOTE: For MVP, relation roles and Child relation types are out of scope. NOTE: If the Relations field is not placed as the meta field but as the content field, StrictDoc shall raise a \`\`StrictDocSemanticError\`\`.

### REQUIREMENT: Valid SDoc node criteria @SDOC-LLR-193

> STATUS: Active

StrictDoc shall recognize a Markdown node as a valid SDoc node when the Markdown node meets the following criteria:

-   The node has one of the meta-fields: MID or UID.
-   The node has an explicit or implicit content field.
-   All node fields, meta or content, have a valid syntax.
-   All node fields, meta or content, are valid default SDoc grammar fields.

### REQUIREMENT: Valid SDoc document root node @SDOC-LLR-200

> STATUS: Active

StrictDoc shall recognize a root Markdown node as a valid SDoc document node when the said Markdown node meets the following criteria:

-   The node has zero or more valid meta-fields.
-   The valid metafields must satisfy \[LINK: SDOC-LLR-194\] and be formatted according to one meta syntax from \[LINK: SDOC-LLR-184\].

**Example: Valid DOCUMENT (title and metadata) + SECTION:**

``` markdown
# Document title

**MID**: abcdabcdabcdabcdabcdabcdabcdabcdabcd \\
**UID**: DOC-001 \\
**Author**: John Doe

## Hello world
```

Such a description shall translate to an SDoc document with:

-   DOCUMENT node with a title \"Document title\" and meta fields (MID, UID, Author).
-   SECTION node with a title \"Hello world\".

**Example: Valid DOCUMENT (title and metadata) + TEXT:**

``` markdown
# Document title

**MID**: abcdabcdabcdabcdabcdabcdabcdabcdabcd \\
**UID**: DOC-001 \\
**Author**: John Doe

Hello world.
```

Such a description shall translate to an SDoc document with:

-   DOCUMENT node with a title \"Document title\" and meta fields (MID, UID, Author).
-   TEXT node with a statement \"Hello world.\".

**Example: Valid DOCUMENT (title, no metadata) + TEXT:**

``` markdown
# Document title

MID: abc

Hello world.
```

Such a description shall translate to an SDoc document with:

-   DOCUMENT node with a title \"Document title\" and no meta fields.

\- TEXT node with a statement \"MID: abc\\\\Hello world.\".

### REQUIREMENT: Reading rules \u2014 Default grammar for MVP @SDOC-LLR-190

> STATUS: Active

When a parsing Markdown file, StrictDoc shall generate an SDoc document using the default SDoc grammar according to the following rules:

-   The only supported node for MVP shall be REQUIREMENT, TEXT and SECTION nodes with no other nodes supported.
-   A valid SDoc node shall be recognized as REQUIREMENT. The Markdown\'s node title becomes the REQUIREMENT node\'s TITLE.
-   If a Markdown node cannot be recognized as a valid SDoc node, the node shall recognize the said Markdown node\'s title as a SECTION node with a TITLE field set to the title and the node\'s body as a regular (non-normative) TEXT SDoc node, not as a normative SDoc node. The TEXT node\'s statement shall contain the Markdown node\'s body.
-   All field names shall be capitalized when created to SDoc field objects. For example, `Statement` becomes `STATEMENT`. At the same time, the original field names must be written to the document\'s grammar as-is. For example, a `**Rationale**:` becomes `RATIONALE` in the SDoc field name and `Rationale` in the human title.
-   StrictDoc shall defer the validation of MID/UID uniqueness across nodes to the TraceabilityIndexBuilder class.
-   If a given field name appears more than once in a node, StrictDoc shall raise a StrictDocSemanticError.
-   If a node is otherwise invalid and also has duplicate fields, the parser shall treat this node as SECTION and TEXT without raising errors.
-   All SDoc node fields, REQUIREMENT/TEXT/SECTION, must store all field values\' Markdown content verbatim, without any pre-processing. This includes preserving original whitespace/line endings exactly.

### REQUIREMENT: Reading rules \u2014 Node hierarchy @SDOC-LLR-199

> STATUS: Active

When a parsing Markdown file, StrictDoc shall generate an SDoc document using the default SDoc grammar according to the following rules:

-   The first content of a Markdown file shall always be a level 1 `#` node with the document title, followed by an optional set of metafields that translate to SDoc document meta (DocumentConfig/custom[metadata]{#metadata}). The syntax for metafields shall be the same to meta fields of a regular markdown node. For MVP, all metafields shall be written as custom[metadata]{#metadata}, with no reserved fields are considered.
-   When the root L1 document title node with (optional meta fields) are recognized, StrictDoc shall treat all following text as a TEXT node until any other header node starts.
-   If StrictDoc can recognize the root L1 document node title but no valid metadata, StrictDoc shall treat all following text as a TEXT node until any other header node starts.
-   When root metadata has a valid syntax but has invalid semantics (duplicated fields), StrictDoc shall raise StrictDocSemanticError.
-   No other node can be at level 1 except the document title, otherwise StrictDocSemanticError must be raised.
-   The Markdown node hierarchy shall be strictly consecutive in forward direction:
    -   If a node level forward jump is encountered, for example L1-\>L3, StrictDoc shall raise a StrictDocSemanticError, regardless of whether the node is valid SDoc node or invalid.
-   The node level jumps in backward direction, for example L4-\>L2, are allowed if the node with a lower level results at level 2 or higher.

### REQUIREMENT: Writing rules \u2014 Default grammar for MVP @SDOC-LLR-198

> STATUS: Active

When writing an SDoc document to a markdown file, StrictDoc shall generate the Markdown markup according to the following rules:

-   The meta fields shall be written:
    -   Using the format #2 for new documents not coming from file system (using backslashes for all meta-field lines but last one).
    -   Using the format that was auto-detected during reading a Markdown file in case the file is already on the disk and follows a certain convention. The detection shall be detected at a file level and memorized individually by each SDoc document.
-   The content fields shall be written using formats #1 (Explicit field name) for single-paragraph fields and #2 (Explicit field name with a line break) for multi-paragraph fields. A multi-paragraph field is one that results in multiple markdown paragraphs/blocks each separated visually by a full empty line.
-   StrictDoc shall write the SDoc fields as Markdown fields based on SDoc human title as recorded in the document grammar element field human title. If a human title is missing in the grammar, the field name shall be used.
-   All fields shall be printed in the same order like they are stored in an SDoc node. Meta vs content decision shall be based on a standard SDocNode/GrammarElement decision for multiline index.
-   The node level shall be used for defining the Markdown node level. The document title becomes the top-level section level 1. SDoc node level 1 becomes `##`, level 2 becomes `###`, etc.

### REQUIREMENT: Robust Markdown backend @SDOC-LLR-187

> STATUS: Active

StrictDoc shall employ a well-maintained Markdown library with Python support.

## HTML2PDF export @SEC-002

### REQUIREMENT: Use of html2pdf4doc @SDOC-LLR-203

> RATIONALE: html2pdf4doc is part of the StrictDoc project that is developed by the core team. It allows printing PDF pages directly from StrictDoc HTML and gives the developers a full control over the printing mechanics.

StrictDoc shall export HTML documents using html2pdf4doc library with the following document types supported already:

-   StrictDoc\'s main DOC document type/screen.

### REQUIREMENT: Use of PyPDF for PDF postprocessing @SDOC-LLR-204

> STATUS: Active

> RATIONALE: The extra processing with PyPDF is needed because there are limitations of what developers can do when printing HTML to PDF with html2pdf4doc based on Google Chrome Driver.

StrictDoc shall employ the PyPDF library for the following tasks:

-   Rewriting all StrictDoc\'s LINK/ANCHOR to documents of the same project tree into the PDF anchors.

### REQUIREMENT: Cross-linking PDF documents from one project tree @SDOC-LLR-205

> STATUS: Active

> RATIONALE: Allows a reader to navigate between PDF documents of the same project as requested by the parent requirement.

> NOTES: The PDF cross-document linking is supported by the PDF format natively but is known to not work in all PDF viewers. For example, it is known to work well in Linux PDF viewers, but not macOS Preview viewer.

When exporting HTML documents to PDF, StrictDoc shall rewrite all LINK/ANCHOR to documents of the same project tree into the PDF document links/anchors according to the following rule: - The Chrome Driver resolves the relative links to other documents with full paths, e.g., \`\`file:///-PDF.html#\`\`. - The PDF postprocessing step shall convert these absolute \`\`file:///\...\` links to just relative paths: \`\`.pdf\`\` without the leading slash character. - If one PDF is in a nested folder compared to another PDF, the link to this PDF anchor shall have relative \`\`../\`\` path components.

## Source code parsing @SEC-003

### Rust @SEC-003.001

#### REQUIREMENT: Auto-scoped relation markers in Rust docs @SDOC-LLR-164

> NOTES: Note that doc comments are syntactic sugar for `doc attribute`_ s, which shall also be supported.
To figure detailed doc comment rules from the rust-lang specification it's sometimes useful
to check for general attribute rules, if explicit doc comment rules are missing.

.. _doc attribute: https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html

If a StrictDoc relation marker is inside a [Rust doc comment](https://doc.rust-lang.org/rust-by-example/meta/doc.html#doc-comments), the marker scope shall be set to exact the item the Rust language defines as target of the containing doc comment. The `@relation(scope=...)` parameter shall therefore be optional and shall be ignored if provided.

``` {.rust .numberLines}
/// @relation(REQ-1)
impl Foo {

    /// @relation(REQ-2)
    fn foo() {
    }
}
```

In the given example, the first marker shall link REQ-1 to the `impl Foo` implementation, highlighting lines 1 to 7. The second marker shall link REQ-2 to the `fn foo()` function, highlighting lines 4 to 6.

#### REQUIREMENT: Inner doc attributes @SDOC-LLR-165

> STATUS: Active

StrictDoc shall support relation markers in [inner](https://doc.rust-lang.org/reference/attributes.html#r-attributes.inner) [doc attribute](https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html#the-doc-attribute) s.

#### REQUIREMENT: Inner line docs @SDOC-LLR-166

> STATUS: Active

StrictDoc shall support auto-scoped relation relation markers in [inner line docs](https://doc.rust-lang.org/reference/comments.html#grammar-INNER_LINE_DOC).

#### REQUIREMENT: Inner block docs @SDOC-LLR-167

> STATUS: Active

StrictDoc shall support auto-scoped relation relation markers in [inner block docs](https://doc.rust-lang.org/reference/comments.html#grammar-INNER_BLOCK_DOC).

#### REQUIREMENT: Outer doc attributes @SDOC-LLR-168

> STATUS: Active

StrictDoc shall support auto-scoped relation markers in [outer](https://doc.rust-lang.org/reference/attributes.html#r-attributes.outer) [doc attribute](https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html#the-doc-attribute) s.

#### REQUIREMENT: Outer line docs @SDOC-LLR-169

> STATUS: Active

StrictDoc shall support auto-scoped relation markers in [outer line docs](https://doc.rust-lang.org/reference/comments.html#grammar-OUTER_LINE_DOC).

#### REQUIREMENT: Outer block docs @SDOC-LLR-170

> STATUS: Active

StrictDoc shall support auto-scoped relation markers in [outer block docs](https://doc.rust-lang.org/reference/comments.html#railroad-OUTER_BLOCK_DOC).

#### REQUIREMENT: File, line and range markers @SDOC-LLR-171

> STATUS: Active

StrictDoc shall point to lines and line ranges of Rust code by using file, line and range markers. These marker types shall be parsed from [regular line and block comments](https://doc.rust-lang.org/rust-by-example/hello/comment.html#comments).

Note: File markers may also result from the inner doc comments of the top-level module.

#### REQUIREMENT: Source nodes from doc comments @SDOC-LLR-172

> STATUS: Active

If a Rust doc comments contains custom tags, and the containing Rust source file matches an entry in the source node configuration, StrictDoc shall create document nodes from the custom tags and automatically link the created node with the Rust item targeted by the doc comment.

#### REQUIREMENT: Forward relations to Rust items @SDOC-LLR-173

> STATUS: Active

StrictDoc shall support linking from a requirement in SDoc to a language item in Rust code by using a `FILE` relation of type `FUNCTION`. For example

``` strictdoc
[REQUIREMENT]
UID: REQ-1
RELATIONS:
- TYPE: File
  VALUE: file.rs
  FUNCTION: file::foo
```

This shall work for all kinds of Rust items that have a [canonical path](https://doc.rust-lang.org/reference/paths.html#canonical-paths), including const, enum, fn, mod, static, struct, trait, type, union.

#### REQUIREMENT: Forward relation by canonical path @SDOC-LLR-174

> STATUS: Active

> NOTES: The canonical path of an item can be observed with :code:`objdump -t lib.o --demangle=rust`. For example, given this
source file

.. code-block:: rust
   :number-lines:

   pub mod foo {

       pub trait Foo {
           fn foo(&self) {}
       }

       pub struct Bar(i32);

       impl Foo for Bar {
           fn foo(&self) {}
       }
   }

:code:`objdump` will show

.. code-block:: shell

   <lib::foo::Bar as lib::foo::Foo>::foo

Alas, a forward relation would be

.. code-block:: strictdoc

   [REQUIREMENT]
   UID: REQ-1
   RELATIONS:
   - TYPE: File
     VALUE: file.rs
     FUNCTION: <lib::foo::Bar as lib::foo::Foo>::foo

The identifier for forward relations shall be the [canonical path](https://doc.rust-lang.org/reference/paths.html#canonical-paths) as the rustc compiler would set it when invoked for a single file like

``` shell
rustc --crate-type rlib --emit=obj src/lib.rs
```

Note: `cargo build` usually result in a different canonical path, since it considers the file position relative to the crate root. Using a single file as root is a simplification, needed because StrictDoc is unaware of the Rust file and directory-based module hierarchy.

#### REQUIREMENT: Collapse doc comments @SDOC-LLR-175

> STATUS: Active

Multiple scattered doc comments shall be collapsed as done by the [rustdoc](https://github.com/rust-lang/rust/tree/main/src/tools/rustdoc) tool when using the collapse-docs option to determine the highlight range(s).

For example, rustdoc would collapse alle these comments into the description of `fn foo()`

``` {.rust .numberLines}
/// Some
/// line

/// doc,

/**
  * and some
  * block dock,
  */

#[doc = "and some"]

#[doc = "doc attr."]

fn foo() {
}
```

In the given example, the StrictDoc highlight range for the relation marker shall be from line 1 to line 16.

#### REQUIREMENT: Rust marker descriptions @SDOC-LLR-176

> STATUS: Active

StrictDoc should use the marker labels as [rustdoc](https://doc.rust-lang.org/stable/rustdoc/) would set them in the description of a documented node.

#### REQUIREMENT: Valid positions of doc comments @SDOC-LLR-177

> STATUS: Active

> NOTES: Since doc comments are syntactic sugar for doc attributes, allowed position rules for attributes apply.

StrictDoc shall find doc comments where the language [allows](https://doc.rust-lang.org/reference/attributes.html#r-attributes.allowed-position) them and ignore those in other positions.

#### REQUIREMENT: Inner doc comments for functions @SDOC-LLR-178

> STATUS: Active

StrictDoc shall find inner doc comments in function blocks.

#### REQUIREMENT: Inner doc comments for modules @SDOC-LLR-179

> STATUS: Active

StrictDoc shall find inner doc comments in module blocks.

#### REQUIREMENT: Inner doc comments for external blocks @SDOC-LLR-180

> STATUS: Active

StrictDoc shall find inner doc comments in external blocks.

#### REQUIREMENT: Inner doc comments for implementation blocks @SDOC-LLR-181

> STATUS: Active

StrictDoc shall find inner doc comments in implementation blocks.

#### REQUIREMENT: Allowed position for outer docs @SDOC-LLR-182

> STATUS: Active

StrictDoc shall find outer doc comments in [allowed positions](https://doc.rust-lang.org/reference/attributes.html#r-attributes.allowed-position) as specified by the Rust language:

-   All [item](https://doc.rust-lang.org/reference/items.html#r-items.syntax) declarations
-   Most statements
-   Block expressions, but only when they are the outer expression of an expression statement or the final expression of another block expression.
-   Enum variants, struct and union fields
-   Generic lifetime or type parameter
-   Expressions in limited situations
-   Function, closure and function pointer parameters
