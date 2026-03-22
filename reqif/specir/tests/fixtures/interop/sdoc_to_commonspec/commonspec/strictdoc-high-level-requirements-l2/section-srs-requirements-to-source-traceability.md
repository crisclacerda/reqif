## SECTION-SRS-Requirements-to-source-traceability @SECTION-SRS-Requirements-to-source-traceability

> ReqIF.ChapterName: Requirements-to-source traceability

### REQUIREMENT: Link requirements with source files @SDOC-SRS-33

> STATUS: Active

StrictDoc shall support bi-directional linking requirements with source files.

### SECTION-f2f8ff49-ea0b-495b-a66e-6eb05ac2ac5d @SECTION-013

> ReqIF.ChapterName: Language-aware parsing of source code

#### REQUIREMENT: Language-aware parsing of source code @SDOC-SRS-142

> RATIONALE: StrictDoc must be capable of traversing the AST of common formats and programming languages to identify and extract function and class markers.

StrictDoc shall support parsing the most commonly used formats and programming languages to the Abstract Syntax Tree (AST) level. The format examples: C, C++, Python, Rust, Ada, Robot, Gherkin, etc.

#### REQUIREMENT: Language-aware parsing of C/C++ code @SDOC-SRS-146

> STATUS: Active

> RATIONALE: C and C++ languages are common languages for embedded and general systems programming. These languages have to be handled with a dedicated parser because of these languages' specifics.

StrictDoc shall support parsing the C and C++ source files which includes: - Recognizing functions and their Doxygen comments. - Recognizing function declarations and function definitions.

#### REQUIREMENT: Language-aware parsing of Python code @SDOC-SRS-147

> STATUS: Active

> RATIONALE: Python language has to be handled with a dedicated parser because of this language's specifics.

StrictDoc shall support parsing the Python source files which includes: - Recognizing Python functions, including nested functions. - Recognizing Python classes, including nested classes. - Recognizing decorated functions.

#### REQUIREMENT: Language-aware parsing of Robot framework code @SDOC-SRS-148

> STATUS: Active

> RATIONALE: Robot framework's markup has to be handled with a dedicated parser because of this language's specifics.

StrictDoc shall support parsing the Robot framework test files.

### SECTION-ef7b0514-5d8a-4399-bbde-2d8c6186fabe @SECTION-014

> ReqIF.ChapterName: Language-aware parsing of Rust source code

#### REQUIREMENT: Auto-scoped relation markers in Rust docs @SDOC-SRS-164

> NOTES: Note that doc comments are syntactic sugar for `doc attribute`_ s, which shall also be supported.
To figure detailed doc comment rules from the rust-lang specification it's sometimes useful
to check for general attribute rules, if explicit doc comment rules are missing.

.. _doc attribute: https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html

If a StrictDoc relation marker is inside a \`Rust doc comment\`\_, the marker scope shall be set to exact the item the Rust language defines as target of the containing doc comment. The :code:\`@relation(scope=\...)\` parameter shall therefore be optional and shall be ignored if provided. .. code-block:: rust :number-lines: /// \@relation(REQ-1) impl Foo { /// \@relation(REQ-2) fn foo() { } } In the given example, the first marker shall link REQ-1 to the :code:\`impl Foo\` implementation, highlighting lines 1 to 7. The second marker shall link REQ-2 to the :code:\`fn foo()\` function, highlighting lines 4 to 6. .. \_Rust doc comment: https://doc.rust-lang.org/rust-by-example/meta/doc.html#doc-comments

[SDOC-SRS-34](@)

[SDOC-SRS-137](@)

#### REQUIREMENT: Inner doc attributes @SDOC-SRS-165

StrictDoc shall support relation markers in inner\_ \`doc attribute\`\_ s. .. \_inner: https://doc.rust-lang.org/reference/attributes.html#r-attributes.inner .. \_doc attribute: https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html#the-doc-attribute

[SDOC-SRS-164](@)

#### REQUIREMENT: Inner line docs @SDOC-SRS-166

StrictDoc shall support auto-scoped relation relation markers in \`inner line docs\`\_. .. \_inner line docs: https://doc.rust-lang.org/reference/comments.html#grammar-INNER_LINE_DOC

[SDOC-SRS-164](@)

#### REQUIREMENT: Inner block docs @SDOC-SRS-167

StrictDoc shall support auto-scoped relation relation markers in \`inner block docs\`\_. .. \_inner block docs: https://doc.rust-lang.org/reference/comments.html#grammar-INNER_BLOCK_DOC

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer doc attributes @SDOC-SRS-168

StrictDoc shall support auto-scoped relation markers in outer\_ \`doc attribute\`\_ s. .. \_outer: https://doc.rust-lang.org/reference/attributes.html#r-attributes.outer .. \_doc attribute: https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html#the-doc-attribute

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer line docs @SDOC-SRS-169

StrictDoc shall support auto-scoped relation markers in \`outer line docs\`\_. .. \_outer line docs: https://doc.rust-lang.org/reference/comments.html#grammar-OUTER_LINE_DOC

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer block docs @SDOC-SRS-170

StrictDoc shall support auto-scoped relation markers in \`outer block docs\`\_. .. \_outer block docs: https://doc.rust-lang.org/reference/comments.html#railroad-OUTER_BLOCK_DOC

[SDOC-SRS-164](@)

#### REQUIREMENT: File, line and range markers @SDOC-SRS-171

StrictDoc shall point to lines and line ranges of Rust code by using file, line and range markers. These marker types shall be parsed from \`regular line and block comments\`\_. Note: File markers may also result from the inner doc comments of the top-level module. .. \_regular line and block comments: https://doc.rust-lang.org/rust-by-example/hello/comment.html#comments

[SDOC-SRS-139](@)

[SDOC-SRS-124](@)

[SDOC-SRS-138](@)

#### REQUIREMENT: Source nodes from doc comments @SDOC-SRS-172

If a Rust doc comments contains custom tags, and the containing Rust source file matches an entry in the source node configuration, StrictDoc shall create document nodes from the custom tags and automatically link the created node with the Rust item targeted by the doc comment.

[SDOC-SRS-141](@)

#### REQUIREMENT: Forward relations to Rust items @SDOC-SRS-173

StrictDoc shall support linking from a requirement in SDoc to a language item in Rust code by using a :code:\`FILE\` relation of type :code:\`FUNCTION\`. For example .. code-block:: strictdoc \[REQUIREMENT\] UID: REQ-1 - TYPE: File VALUE: file.rs FUNCTION: file::foo This shall work for all kinds of Rust items that have a \`canonical path\`\_, including const, enum, fn, mod, static, struct, trait, type, union. .. \_canonical path: https://doc.rust-lang.org/reference/paths.html#canonical-paths

#### REQUIREMENT: Forward relation by canonical path @SDOC-SRS-174

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
   - TYPE: File
     VALUE: file.rs
     FUNCTION: <lib::foo::Bar as lib::foo::Foo>::foo

The identifier for forward relations shall be the \`canonical path\`\_ as the rustc compiler would set it when invoked for a single file like .. code-block:: shell rustc \--crate-type rlib \--emit=obj src/lib.rs Note: :code:\`cargo build\` usually result in a different canonical path, since it considers the file position relative to the crate root. Using a single file as root is a simplification, needed because StrictDoc is unaware of the Rust file and directory-based module hierarchy. .. \_canonical path: https://doc.rust-lang.org/reference/paths.html#canonical-paths

[SDOC-SRS-173](@)

#### REQUIREMENT: Collapse doc comments @SDOC-SRS-175

Multiple scattered doc comments shall be collapsed as done by the rustdoc\_ tool when using the collapse-docs option to determine the highlight range(s). For example, rustdoc would collapse alle these comments into the description of :code:\`fn foo()\` .. code-block:: rust :number-lines: /// Some /// line /// doc, /\*\* \* and some \* block dock, \*/ #\[doc = \"and some\"\] #\[doc = \"doc attr.\"\] fn foo() { } In the given example, the StrictDoc highlight range for the relation marker shall be from line 1 to line 16. .. \_rustdoc: https://github.com/rust-lang/rust/tree/main/src/tools/rustdoc

#### REQUIREMENT: Rust marker descriptions @SDOC-SRS-176

StrictDoc should use the marker labels as rustdoc\_ would set them in the description of a documented node. .. \_rustdoc: https://doc.rust-lang.org/stable/rustdoc/

#### REQUIREMENT: Valid positions of doc comments @SDOC-SRS-177

> NOTES: Since doc comments are syntactic sugar for doc attributes, allowed position rules for attributes apply.

StrictDoc shall find doc comments where the language allows\_ them and ignore those in other positions. .. \_allows: https://doc.rust-lang.org/reference/attributes.html#r-attributes.allowed-position

#### REQUIREMENT: Inner doc comments for functions @SDOC-SRS-178

StrictDoc shall find inner doc comments in function blocks.

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for modules @SDOC-SRS-179

StrictDoc shall find inner doc comments in module blocks.

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for external blocks @SDOC-SRS-180

StrictDoc shall find inner doc comments in external blocks.

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for implementation blocks @SDOC-SRS-181

StrictDoc shall find inner doc comments in implementation blocks.

[SDOC-SRS-177](@)

#### REQUIREMENT: Allowed position for outer docs @SDOC-SRS-182

StrictDoc shall find outer doc comments in \`allowed positions\`\_ as specified by the Rust language: - All item\_ declarations - Most statements - Block expressions, but only when they are the outer expression of an expression statement or the final expression of another block expression. - Enum variants, struct and union fields - Generic lifetime or type parameter - Expressions in limited situations - Function, closure and function pointer parameters .. \_allowed positions: https://doc.rust-lang.org/reference/attributes.html#r-attributes.allowed-position .. \_item: https://doc.rust-lang.org/reference/items.html#r-items.syntax

[SDOC-SRS-177](@)

### REQUIREMENT: Link requirements with test files and test reports @SDOC-SRS-143

> STATUS: Active

> RATIONALE: Tracing requirements to not just test files but also the test report information closes the verification cycle more completely.

StrictDoc shall support bi-directional linking between requirements, test files, and test reports.

### REQUIREMENT: Link requirements with code coverage information @SDOC-SRS-144

> STATUS: Active

> RATIONALE: Tracing requirements to not just test files but also to the code coverage information closes the verification cycle more completely.

StrictDoc shall support linking between requirements, source files, and code coverage information.

### SECTION-cf55b051-89a5-460a-99e5-075eb4602bd4 @SECTION-015

> ReqIF.ChapterName: Forward linking from requirements to source code

#### REQUIREMENT: SDoc markup's forward relations @SDOC-SRS-145

> RATIONALE: There are cases when it is not possible to modify source code directly. The forward linking enables to refer to the files or their parts from SDoc nodes. Depending on a project structure, the forward linking from requirements to source files can replace the backward linking from source code back to requirements, or both approaches can co-exist.

StrictDoc shall support forward linking from SDoc nodes to source files.

### SECTION-91ed1a93-b95e-41e6-8e3d-57e05086b85d @SECTION-016

> ReqIF.ChapterName: Source code markup \u2013 Relations

#### REQUIREMENT: Relation markers syntax @SDOC-SRS-34

> STATUS: Active

StrictDoc shall support annotating source code with links that reference the requirements.

#### REQUIREMENT: Line marker @SDOC-SRS-124

> STATUS: Active

> RATIONALE: Sometimes a requirement can influence only a single line in the source code. The advantage of a single-line marker compared to a range marker is that a single-line marker is not intrusive and does not clutter source code.

StrictDoc\'s shall support line markers that can be attached to single source code lines. NOTE: A single-line marker points to a single line in a source file.

#### REQUIREMENT: Function marker @SDOC-SRS-137

> STATUS: Active

> RATIONALE: A function is a basic building block of most programming language. It is straightforward to match a source code function to one or more related requirements.

StrictDoc shall support relation markers that can be attached to individual source code functions.

#### REQUIREMENT: Class marker @SDOC-SRS-140

> STATUS: Active

> RATIONALE: A class is a basic building block of most programming language. Some requirements can be naturally attached to the whole classes.

> NOTES: Not all programming languages support classes, e.g., C. For these languages and non-code text files, the class markers will have no effect.

StrictDoc shall support relation markers that can be attached to source code classes.

#### REQUIREMENT: File marker @SDOC-SRS-139

> STATUS: Active

> RATIONALE: There are cases when a requirement can be attached to an entire file.

StrictDoc\'s shall support file markers that can be attached to entire source files.

#### REQUIREMENT: Range marker @SDOC-SRS-138

> STATUS: Active

> RATIONALE: There are cases when a requirement implementation results in the requirement affecting only a range/block of source code.

StrictDoc shall support relation markers that can be attached to source code ranges. NOTE: Compared to other marker types, to indicate a range, two markers are needed: one to start a range and one to end a range.

### SECTION-d7214878-e16d-4e35-a472-170d8f8be10f @SECTION-017

> ReqIF.ChapterName: Source code markup \u2013 Nodes

#### REQUIREMENT: Parse nodes from source code @SDOC-SRS-141

> STATUS: Active

> RATIONALE: It can be practical to define the requirement and other nodes directly in source comments and then let a requirements tool generate documents from these nodes' content automatically.

A reference example: Generating test specifications from the TEST_SPEC nodes which are defined directly in source code comments.

StrictDoc shall support parsing nodes from source code.
