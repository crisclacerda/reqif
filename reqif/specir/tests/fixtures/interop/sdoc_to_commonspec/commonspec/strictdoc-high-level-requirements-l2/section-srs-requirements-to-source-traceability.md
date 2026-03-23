## SECTION-SRS-Requirements-to-source-traceability @SECTION-SRS-Requirements-to-source-traceability

> ReqIF.ChapterName: Requirements-to-source traceability

### REQUIREMENT: Link requirements with source files @SDOC-SRS-33

> STATUS: Active

### SECTION-6b4d8ce4-f039-4324-addb-bac254862385 @SECTION-013

> ReqIF.ChapterName: Language-aware parsing of source code

#### REQUIREMENT: Language-aware parsing of source code @SDOC-SRS-142

> RATIONALE: StrictDoc must be capable of traversing the AST of common formats and programming languages to identify and extract function and class markers.

#### REQUIREMENT: Language-aware parsing of C/C++ code @SDOC-SRS-146

> STATUS: Active

> RATIONALE: C and C++ languages are common languages for embedded and general systems programming. These languages have to be handled with a dedicated parser because of these languages' specifics.

#### REQUIREMENT: Language-aware parsing of Python code @SDOC-SRS-147

> STATUS: Active

> RATIONALE: Python language has to be handled with a dedicated parser because of this language's specifics.

#### REQUIREMENT: Language-aware parsing of Robot framework code @SDOC-SRS-148

> STATUS: Active

> RATIONALE: Robot framework's markup has to be handled with a dedicated parser because of this language's specifics.

### SECTION-79e46539-8efe-4222-9645-4a7261ce09b7 @SECTION-014

> ReqIF.ChapterName: Language-aware parsing of Rust source code

#### REQUIREMENT: Auto-scoped relation markers in Rust docs @SDOC-SRS-164

> NOTES: Note that doc comments are syntactic sugar for `doc attribute`_ s, which shall also be supported.
To figure detailed doc comment rules from the rust-lang specification it's sometimes useful
to check for general attribute rules, if explicit doc comment rules are missing.

.. _doc attribute: https://doc.rust-lang.org/rustdoc/write-documentation/the-doc-attribute.html

[SDOC-SRS-34](@)

[SDOC-SRS-137](@)

#### REQUIREMENT: Inner doc attributes @SDOC-SRS-165

[SDOC-SRS-164](@)

#### REQUIREMENT: Inner line docs @SDOC-SRS-166

[SDOC-SRS-164](@)

#### REQUIREMENT: Inner block docs @SDOC-SRS-167

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer doc attributes @SDOC-SRS-168

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer line docs @SDOC-SRS-169

[SDOC-SRS-164](@)

#### REQUIREMENT: Outer block docs @SDOC-SRS-170

[SDOC-SRS-164](@)

#### REQUIREMENT: File, line and range markers @SDOC-SRS-171

[SDOC-SRS-139](@)

[SDOC-SRS-124](@)

[SDOC-SRS-138](@)

#### REQUIREMENT: Source nodes from doc comments @SDOC-SRS-172

[SDOC-SRS-141](@)

#### REQUIREMENT: Forward relations to Rust items @SDOC-SRS-173

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

[SDOC-SRS-173](@)

#### REQUIREMENT: Collapse doc comments @SDOC-SRS-175

#### REQUIREMENT: Rust marker descriptions @SDOC-SRS-176

#### REQUIREMENT: Valid positions of doc comments @SDOC-SRS-177

> NOTES: Since doc comments are syntactic sugar for doc attributes, allowed position rules for attributes apply.

#### REQUIREMENT: Inner doc comments for functions @SDOC-SRS-178

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for modules @SDOC-SRS-179

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for external blocks @SDOC-SRS-180

[SDOC-SRS-177](@)

#### REQUIREMENT: Inner doc comments for implementation blocks @SDOC-SRS-181

[SDOC-SRS-177](@)

#### REQUIREMENT: Allowed position for outer docs @SDOC-SRS-182

[SDOC-SRS-177](@)

### REQUIREMENT: Link requirements with test files and test reports @SDOC-SRS-143

> STATUS: Active

> RATIONALE: Tracing requirements to not just test files but also the test report information closes the verification cycle more completely.

### REQUIREMENT: Link requirements with code coverage information @SDOC-SRS-144

> STATUS: Active

> RATIONALE: Tracing requirements to not just test files but also to the code coverage information closes the verification cycle more completely.

### SECTION-91676088-c32f-4362-8ba9-bfe05f6f3faf @SECTION-015

> ReqIF.ChapterName: Forward linking from requirements to source code

#### REQUIREMENT: SDoc markup's forward relations @SDOC-SRS-145

> RATIONALE: There are cases when it is not possible to modify source code directly. The forward linking enables to refer to the files or their parts from SDoc nodes. Depending on a project structure, the forward linking from requirements to source files can replace the backward linking from source code back to requirements, or both approaches can co-exist.

### SECTION-fa23be4a-3424-4d11-bac9-fd1920a7f336 @SECTION-016

> ReqIF.ChapterName: Source code markup \u2013 Relations

#### REQUIREMENT: Relation markers syntax @SDOC-SRS-34

> STATUS: Active

#### REQUIREMENT: Line marker @SDOC-SRS-124

> STATUS: Active

> RATIONALE: Sometimes a requirement can influence only a single line in the source code. The advantage of a single-line marker compared to a range marker is that a single-line marker is not intrusive and does not clutter source code.

#### REQUIREMENT: Function marker @SDOC-SRS-137

> STATUS: Active

> RATIONALE: A function is a basic building block of most programming language. It is straightforward to match a source code function to one or more related requirements.

#### REQUIREMENT: Class marker @SDOC-SRS-140

> STATUS: Active

> RATIONALE: A class is a basic building block of most programming language. Some requirements can be naturally attached to the whole classes.

> NOTES: Not all programming languages support classes, e.g., C. For these languages and non-code text files, the class markers will have no effect.

#### REQUIREMENT: File marker @SDOC-SRS-139

> STATUS: Active

> RATIONALE: There are cases when a requirement can be attached to an entire file.

#### REQUIREMENT: Range marker @SDOC-SRS-138

> STATUS: Active

> RATIONALE: There are cases when a requirement implementation results in the requirement affecting only a range/block of source code.

### SECTION-a00999b9-d625-42cc-b5cc-53d06f17645f @SECTION-017

> ReqIF.ChapterName: Source code markup \u2013 Nodes

#### REQUIREMENT: Parse nodes from source code @SDOC-SRS-141

> STATUS: Active

> RATIONALE: It can be practical to define the requirement and other nodes directly in source comments and then let a requirements tool generate documents from these nodes' content automatically.

A reference example: Generating test specifications from the TEST_SPEC nodes which are defined directly in source code comments.
