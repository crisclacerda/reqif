## SECTION-SSRS-Performance @SECTION-SSRS-Performance

> ReqIF.ChapterName: Performance

### REQUIREMENT: Process-based parallelization @SDOC-SRS-1

> STATUS: Active

> RATIONALE: Process-based parallelization can provide a good speed-up when several large documents have to be generated.

### REQUIREMENT: Caching of parsed SDoc documents @SDOC-SRS-95

> STATUS: Active

### REQUIREMENT: Incremental generation of documents @SDOC-SRS-2

> STATUS: Active

### REQUIREMENT: Caching of RST fragments @SDOC-SRS-3

> STATUS: Active

> RATIONALE: Conversion of RST markup to HTML is a time consuming process. Caching the rendered HTML of each fragment helps to save time when rendering the HTML content.

### REQUIREMENT: On-demand loading of HTML pages @SDOC-SRS-4

> STATUS: Active

> RATIONALE: Generating a whole documentation tree for a user project can be time consuming. The on-demand loading ensures the "do less work" approach when it comes to rendering the HTML pages.

### REQUIREMENT: Precompiled Jinja templates @SDOC-SRS-5

> STATUS: Active

> RATIONALE: The StrictDoc-exported HTML content visible to a user is assembled from numerous small HTML fragments. Precompiling the HTML templates from which the content gets rendered improves the performance of the HTML rendering.
