## SECTION-bf63ec1b-c102-4f77-a8ac-9b4cbe3915c1 @SECTION-002

> ReqIF.ChapterName: SDoc text markup

### REQUIREMENT: SDoc markup language @SDOC-SRS-20

> STATUS: Active

> RATIONALE: The most commonly used Markdown format lacks the ability to store requirements metadata. While the RST syntax does allow for customization with directives to implement metadata extensions, its visual appearance contradicts other requirements of StrictDoc, such as the type-safety of the grammar and visual readability. Therefore, a markup language tailored specifically to the needs of the requirements tool provides direct control over the capabilities implemented in both the markup and the user interface.

### REQUIREMENT: Identical SDoc content by import/export roundtrip @SDOC-SRS-136

> STATUS: Active

> RATIONALE: A consistent import/export roundtrip implementation and testing reduces the risk of the SDoc bi-directional import/export corruption.

### REQUIREMENT: SDoc and Git storage @SDOC-SRS-127

> STATUS: Active

### REQUIREMENT: SDoc file extension @SDOC-SRS-104

> STATUS: Active

> RATIONALE: Given that the name of the model is S-Doc (strict-doc), it is reasonable to make the document files have the ``.sdoc`` extension. This helps to identify the document files.

### REQUIREMENT: One document per one SDoc file @SDOC-SRS-105

> STATUS: Active

> NOTES: A "Document" corresponds to a "Document" of the SDoc data model.

### REQUIREMENT: Fixed grammar @SDOC-SRS-19

> STATUS: Active

### REQUIREMENT: Default grammar fields @SDOC-SRS-93

> STATUS: Active

### REQUIREMENT: Custom grammar / fields @SDOC-SRS-21

> STATUS: Active

> RATIONALE: A custom grammar allows a user to define their own configuration of requirement fields.

### REQUIREMENT: Importable grammars @SDOC-SRS-122

> STATUS: Active

> RATIONALE: A single grammar defined for several documents helps to standardize the structure of all documents in a documentation tree and removes the effort needed to create identical grammars all the time.

### REQUIREMENT: UID identifier format @SDOC-SRS-22

> STATUS: Active

> RATIONALE: A standardized UID format supports easier unique identification of requirements. It is easier to visually identify UIDs that look similar and common to a given industry.

> NOTES: This requirement may need a revision to accommodate for more UID formats.

### REQUIREMENT: Format-specific markup-to-HTML fragment writers @SDOC-SRS-24

> STATUS: Active

### REQUIREMENT: MathJAX @SDOC-SRS-27

> STATUS: Active

### REQUIREMENT: No indentation @SDOC-SRS-23

> STATUS: Active

> RATIONALE: Nesting large text blocks of free text and requirements compromises readability.

### REQUIREMENT: Type-safe fields @SDOC-SRS-25

> STATUS: Active
