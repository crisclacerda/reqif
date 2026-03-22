## SECTION-SRS-Export-import-formats @SECTION-SRS-Export-import-formats

> ReqIF.ChapterName: Export/import formats

### SECTION-SRS-RST @SECTION-SRS-RST

> ReqIF.ChapterName: RST

#### REQUIREMENT: Export to RST @SDOC-SRS-70

> STATUS: Active

> RATIONALE: Exporting SDoc content to RST enables:

1) Generating RST to Sphinx HTML documentation.
2) Generating RST to PDF using Sphinx/LaTeX.

StrictDoc shall allow exporting SDoc content to the RST format.

#### REQUIREMENT: Docutils @SDOC-SRS-71

> STATUS: Active

> RATIONALE: Docutils is the most mature RST-to-HTML converter.

> NOTES: TBD: Move this to design decisions.

StrictDoc shall generate RST markup to HTML using Docutils.

### SECTION-SRS-ReqIF @SECTION-SRS-ReqIF

> ReqIF.ChapterName: ReqIF

#### REQUIREMENT: Export/import from/to ReqIF @SDOC-SRS-72

> STATUS: Active

StrictDoc shall support exporting/importing requirements content from/to ReqIF format.

#### REQUIREMENT: Standalone ReqIF layer @SDOC-SRS-73

> STATUS: Active

> RATIONALE: ReqIF is a well-defined standard which exists independently of StrictDoc's development. It is reasonable to maintain the ReqIF codebase as a separate software component to allow independent development and easier maintainability.

StrictDoc shall maintain the core ReqIF implementation as a separate software component.

### SECTION-SRS-Excel @SECTION-SRS-Excel

> ReqIF.ChapterName: Excel and CSV

#### REQUIREMENT: Export to Excel @SDOC-SRS-74

> STATUS: Active

StrictDoc shall allow exporting SDoc documents to Excel, one Excel sheet per document.

#### REQUIREMENT: Import from Excel @SDOC-SRS-152

> STATUS: Active

StrictDoc shall allow importing Excel documents to SDoc documents, one Excel sheet per document.

#### REQUIREMENT: Selected fields export @SDOC-SRS-134

> STATUS: Active

StrictDoc Excel export shall allow exporting SDoc documents to Excel with only selected fields.
