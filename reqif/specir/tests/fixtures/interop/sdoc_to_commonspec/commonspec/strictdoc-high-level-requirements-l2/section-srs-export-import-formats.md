## SECTION-SRS-Export-import-formats @SECTION-SRS-Export-import-formats

> ReqIF.ChapterName: Export/import formats

### SECTION-SRS-RST @SECTION-SRS-RST

> ReqIF.ChapterName: RST

#### REQUIREMENT: Export to RST @SDOC-SRS-70

> STATUS: Active

> RATIONALE: Exporting SDoc content to RST enables:

1) Generating RST to Sphinx HTML documentation.
2) Generating RST to PDF using Sphinx/LaTeX.

#### REQUIREMENT: Docutils @SDOC-SRS-71

> STATUS: Active

> RATIONALE: Docutils is the most mature RST-to-HTML converter.

> NOTES: TBD: Move this to design decisions.

### SECTION-SRS-ReqIF @SECTION-SRS-ReqIF

> ReqIF.ChapterName: ReqIF

#### REQUIREMENT: Export/import from/to ReqIF @SDOC-SRS-72

> STATUS: Active

#### REQUIREMENT: Standalone ReqIF layer @SDOC-SRS-73

> STATUS: Active

> RATIONALE: ReqIF is a well-defined standard which exists independently of StrictDoc's development. It is reasonable to maintain the ReqIF codebase as a separate software component to allow independent development and easier maintainability.

### SECTION-SRS-Excel @SECTION-SRS-Excel

> ReqIF.ChapterName: Excel and CSV

#### REQUIREMENT: Export to Excel @SDOC-SRS-74

> STATUS: Active

#### REQUIREMENT: Import from Excel @SDOC-SRS-152

> STATUS: Active

#### REQUIREMENT: Selected fields export @SDOC-SRS-134

> STATUS: Active
