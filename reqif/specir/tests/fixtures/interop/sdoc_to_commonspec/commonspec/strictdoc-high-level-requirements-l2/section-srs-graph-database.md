## SECTION-SRS-Graph-database @SECTION-SRS-Graph-database

> ReqIF.ChapterName: Graph database

### REQUIREMENT: Traceability index @SDOC-SRS-28

> STATUS: Active

StrictDoc shall maintain a complete Traceability Index of all documentation- and requirements-related information available in a project tree.

### REQUIREMENT: Uniqueness UID in tree @SDOC-SRS-29

> STATUS: Active

> RATIONALE: The requirement ensures that the Traceability Index takes of care of validating the uniqueness of all nodes in a document/requirements graph.

For each requirement node, the Traceability Index shall ensure its uniqueness throughout the node\'s lifecycle.

### REQUIREMENT: Detect links cycles @SDOC-SRS-30

> STATUS: Active

The Traceability Index shall detect cycles between requirements.

### REQUIREMENT: Link document nodes @SDOC-SRS-32

> STATUS: Active

> RATIONALE: The relations between all documents are a summary of all relations between these documents' requirements. This information is useful for:

1) Structural analysis of a requirements/documents graph.
2) Incremental regeneration of only those documents whose content was modified.

The Traceability Index shall recognize and maintain the relations between all documents of a project tree.

### REQUIREMENT: Automatic resolution of reverse relations @SDOC-SRS-102

> STATUS: Active

> RATIONALE: The calculation of the reverse relations allows the user interface code to get and display both requirement's parent and child relations.

> NOTES: Example: If a child requirement REQ-002 has a parent requirement REQ-001, the graph database first reads the link ``REQ-002 -Parent> REQ-001``, then it creates a corresponding ``REQ-001 -Child> REQ-002`` on the go. Both relations can be queried as follows, in pseudocode:

.. code-block::

    get_parent_requirements(REQ-002) == [REQ-001]
    get_children_requirements(REQ-001) == [REQ-002]

The StrictDoc\'s graph database shall maintain the requirement relations and their reverse relations as follows: - For a Parent relation, the database shall calculate the reverse Child relation. - For a Child relation, the database shall calculate the reverse Parent relation.
