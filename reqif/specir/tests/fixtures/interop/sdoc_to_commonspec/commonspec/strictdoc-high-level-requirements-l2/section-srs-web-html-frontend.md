## Web/HTML frontend @SECTION-SRS-Web-HTML-frontend

### General export requirements @SECTION-SRS-General-export-requirements-2

#### REQUIREMENT: Export to static HTML website @SDOC-SRS-49

> STATUS: Active

StrictDoc shall support generating requirements documentation into static HTML.

#### REQUIREMENT: Web interface @SDOC-SRS-50

> STATUS: Active

StrictDoc shall provide a web interface.

#### REQUIREMENT: Multi-user editing of documents @SDOC-SRS-123

> STATUS: Active

StrictDoc shall support concurrent use and editing of a single StrictDoc web server instance by multiple users.

#### REQUIREMENT: Preserve generated file names @SDOC-SRS-48

> STATUS: Active

> RATIONALE: Name preservation helps to visually identify which input file an output file corresponds to.

For all export operations, StrictDoc shall maintain the original filenames of the documents when producing output files.

### Screen: Project tree @SECTION-SRS-Screen-Project-tree

#### REQUIREMENT: View project tree @SDOC-SRS-53

> STATUS: Active

> RATIONALE: This screen is the main tool for visualizing the project tree structure.

StrictDoc\'s \"Project tree\" screen shall provide browsing of a documentation project tree.

#### REQUIREMENT: Create document @SDOC-SRS-107

> STATUS: Active

StrictDoc\'s Project Tree screen shall allow creating documents.

#### REQUIREMENT: Delete document @SDOC-SRS-108

> STATUS: Active

StrictDoc\'s Project Tree screen shall allow deleting documents.

### Screen: Document (DOC) @SECTION-SRS-Screen-Document-DOC

#### REQUIREMENT: Format-specific document handling @SDOC-SRS-201

> STATUS: Active

StrictDoc\'s Document screen shall arrange all CRUD operations according to the input document format.

Example: If an SDoc document is read from a Markdown file using a dedicated reader, it shall be written back using a Markdown writer.

#### REQUIREMENT: Read document @SDOC-SRS-54

> STATUS: Active

StrictDoc\'s Document screen shall allow reading documents.

#### REQUIREMENT: Create node @SDOC-SRS-106

> STATUS: Active

StrictDoc\'s Document screen shall allow creating document nodes.

#### REQUIREMENT: Clone node from existing node @SDOC-SRS-161

> STATUS: Active

> RATIONALE: Simplifies the creation of similar nodes.

StrictDoc shall support cloning nodes from existing nodes.

#### REQUIREMENT: Update node @SDOC-SRS-55

> STATUS: Active

StrictDoc\'s Document screen shall allow update document content.

#### REQUIREMENT: Delete node @SDOC-SRS-162

> STATUS: Active

StrictDoc\'s Document screen shall support the deletion of document nodes.

#### REQUIREMENT: Create node relation @SDOC-SRS-159

> STATUS: Active

StrictDoc\'s Document screen shall creating updating node relations.

#### REQUIREMENT: Update node relation @SDOC-SRS-158

> STATUS: Active

StrictDoc\'s Document screen shall allow updating node relations.

#### REQUIREMENT: Move requirement / section nodes within document @SDOC-SRS-92

> STATUS: Active

> RATIONALE: Moving the nodes within a document is a convenience feature that speeds up the requirements editing process significantly.

StrictDoc\'s Document screen shall provide a capability to move the nodes within a document.

#### REQUIREMENT: Edit Document grammar @SDOC-SRS-56

> STATUS: Active

> RATIONALE: Editing document grammar allows a user to customize the requirements fields.

StrictDoc\'s screen shall allow editing a document\'s grammar.

#### REQUIREMENT: Edit Document options @SDOC-SRS-57

> STATUS: Active

StrictDoc\'s Document screen shall provide controls for configuring the document-specific options.

#### REQUIREMENT: Auto-generate requirements UIDs @SDOC-SRS-96

> STATUS: Active

StrictDoc\'s Document screen shall provide controls for automatic generation of requirements UIDs.

#### REQUIREMENT: Auto-completion for requirements UIDs @SDOC-SRS-120

> STATUS: Active

> NOTES: The automatic completion can be especially useful when a user has to fill in a parent relation UID.

StrictDoc\'s Document screen shall provide controls for automatic completion of requirements UIDs.

#### REQUIREMENT: Buttons to copy text to buffer @SDOC-SRS-59

> STATUS: Active

StrictDoc shall provide a \"copy text to buffer\" button for all requirement\'s text fields.

### Screen: Table (TBL) @SECTION-SRS-Screen-Table-TBL

#### REQUIREMENT: View TBL screen @SDOC-SRS-62

> STATUS: Active

StrictDoc\'s Table screen shall allow reading documents in a table-like manner.

### Screen: Traceability (TR) @SECTION-SRS-Screen-Traceability-TR

#### REQUIREMENT: View TR screen @SDOC-SRS-65

> STATUS: Active

StrictDoc shall provide a single document-level traceability screen.

NOTE: This screen helps to read a document like a normal document while the traceability to this document\'s parent and child elements is visible at the same time.

### Screen: Deep traceability (DTR) @SECTION-SRS-Screen-Deep-traceability-DTR

#### REQUIREMENT: View DTR screen @SDOC-SRS-66

> STATUS: Active

StrictDoc shall provide a deep traceability screen.

### Screen: HTML2PDF @SEC-006.007

#### REQUIREMENT: Export to HTML content to PDF (HTML2PDF) @SDOC-SRS-51

> STATUS: Active

> RATIONALE: As required by the parent requirement, PDF is one of the most common documentation formats.

StrictDoc shall allow exporting documents and entire documentation trees to PDF.

#### REQUIREMENT: Cross-linking PDF documents from same project tree @SDOC-SRS-203

> STATUS: Active

> RATIONALE: This enables navigation between PDF documents within the same project tree, which can be useful for simplifying the review and tracing work performed by readers.

When exporting multiple HTML documents from a same project tree into PDF, StrictDoc shall preserve all cross-document linking in the output PDF documents.

#### REQUIREMENT: Custom PDF export template @SDOC-SRS-160

> STATUS: Active

StrictDoc shall support the customization of the PDF export template.

### Screen: Project statistics @SEC-006.008

#### REQUIREMENT: Display project statistics @SDOC-SRS-97

> STATUS: Active

> RATIONALE: TBD

StrictDoc shall provide a Project Statistics screen that displays the following project information:

-   Project title
-   Date of generation
-   Git revision
-   Total documents
-   Total requirements
-   Requirements status breakdown
-   Total number of TBD/TBC found in documents.

#### REQUIREMENT: Support for user-provided custom statistics generators @SDOC-SRS-154

> STATUS: Active

> RATIONALE: Projects often have unique traceability and reporting requirements, and supporting custom statistics allows StrictDoc to display metrics that are most relevant to each project's context.

StrictDoc shall support customization of the project statistics screen, enabling users to define and display their own project-specific statistics.

### Screen: Document tree map @SEC-006.009

#### REQUIREMENT: Tree map @SDOC-SRS-157

> STATUS: Active

> RATIONALE: Enables the visualization and browsing of the overall document tree and requirements coverage information.

StrictDoc shall provide a tree map screen, visualizing the following information:

-   Document tree map
-   Requirements coverage by source code
-   Requirements coverage by test files.

### Screen: Source coverage @SEC-006.010

#### REQUIREMENT: Project source code coverage @SDOC-SRS-35

> STATUS: Active

StrictDoc shall generate project source code coverage information.

NOTE: Source code information can be visualized using both web or CLI interfaces.

### Screen: Single source file coverage @SEC-006.011

#### REQUIREMENT: Single source file coverage @SDOC-SRS-36

> STATUS: Active

> RATIONALE: With this capability in place, it is possible to focus on a single implementation file's links to requirements which helps in the code reviews and inspections.

StrictDoc shall generate single file traceability information.

### Screen: Traceability matrix @SEC-006.012

#### REQUIREMENT: Traceability matrix @SDOC-SRS-112

> STATUS: Active

StrictDoc shall provide a traceability matrix screen.

### Screen: Project tree diff @SEC-006.013

#### REQUIREMENT: Project tree diff @SDOC-SRS-111

> STATUS: Active

StrictDoc shall provide a project tree diff screen.

### Content search @SEC-006.014

#### REQUIREMENT: Content search @SDOC-SRS-155

> STATUS: Active

> RATIONALE: As per the parent requirement, a search bar with query support enables users to interactively find specific content without navigating the entire documentation tree.

StrictDoc shall provide searching documentation content with queries via a search bar.
