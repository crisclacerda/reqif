## Performance @SECTION-SSRS-Performance

### REQUIREMENT: Process-based parallelization @SDOC-SRS-1

> STATUS: Active

> RATIONALE: Process-based parallelization can provide a good speed-up when several large documents have to be generated.

StrictDoc shall support process-based parallelization for time-critical tasks.

### REQUIREMENT: Caching of parsed SDoc documents @SDOC-SRS-95

> STATUS: Active

StrictDoc shall implement caching of parsed SDoc documents.

### REQUIREMENT: Incremental generation of documents @SDOC-SRS-2

> STATUS: Active

StrictDoc shall support incremental generation of documents.

NOTE: \"Incremental\" means that only the modified documents are regenerated when StrictDoc is run repeatedly against the same project tree.

### REQUIREMENT: Caching of RST fragments @SDOC-SRS-3

> STATUS: Active

> RATIONALE: Conversion of RST markup to HTML is a time consuming process. Caching the rendered HTML of each fragment helps to save time when rendering the HTML content.

StrictDoc shall cache the RST fragments rendered to HTML.

### REQUIREMENT: On-demand loading of HTML pages @SDOC-SRS-4

> STATUS: Active

> RATIONALE: Generating a whole documentation tree for a user project can be time consuming. The on-demand loading ensures the "do less work" approach when it comes to rendering the HTML pages.

StrictDoc\'s web interface shall generate the HTML content only when it is directly requested by a user.

### REQUIREMENT: Precompiled Jinja templates @SDOC-SRS-5

> STATUS: Active

> RATIONALE: The StrictDoc-exported HTML content visible to a user is assembled from numerous small HTML fragments. Precompiling the HTML templates from which the content gets rendered improves the performance of the HTML rendering.

StrictDoc shall support a precompilation of HTML templates.
