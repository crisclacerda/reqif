"""Convert SpecIR body content (Pandoc AST JSON or HTML) to CommonSpec Markdown.

Two source formats are handled:

* **Pandoc AST JSON** (``spec_objects.ast``, ``spec_attribute_values.ast``) —
  stored by SpecCompiler's Lua pipeline.  Converted via
  ``pandoc -f json -t markdown``.

* **HTML fragments** (``spec_objects.content_xhtml``,
  ``spec_attribute_values.xhtml_value``) — stored by the ReqIF importer.
  Converted via ``pandoc -f html -t markdown``.

Both paths use a Pandoc subprocess for conversion.  If Pandoc is unavailable
the functions fall back to returning the raw content unchanged.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Optional


# ── Pandoc location ──────────────────────────────────────────────────────

def _find_pandoc() -> Optional[str]:
    """Locate the Pandoc binary.

    Search order:
    1. ``dist/bin/pandoc`` relative to the SpecCompiler source tree
    2. ``SPECCOMPILER_HOME/dist/bin/pandoc`` (runtime installation)
    3. System PATH
    """
    # Relative to this file:  …/dist/vendor/python/reqif/specir/ → …/dist/bin/
    here = os.path.dirname(os.path.abspath(__file__))
    dist_bin = os.path.normpath(os.path.join(here, "..", "..", "..", "..", "bin", "pandoc"))
    if os.path.isfile(dist_bin) and os.access(dist_bin, os.X_OK):
        return dist_bin

    sc_home = os.environ.get("SPECCOMPILER_HOME")
    if sc_home:
        p = os.path.join(sc_home, "dist", "bin", "pandoc")
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    return shutil.which("pandoc")


# Module-level cached path (resolved once per process).
_pandoc_path: Optional[str] = None
_pandoc_resolved = False


def get_pandoc() -> Optional[str]:
    """Return the absolute path to the Pandoc binary, or *None*."""
    global _pandoc_path, _pandoc_resolved
    if not _pandoc_resolved:
        _pandoc_path = _find_pandoc()
        _pandoc_resolved = True
    return _pandoc_path


# ── AST cleanup ──────────────────────────────────────────────────────────

def _clean_ast_blocks(blocks: list, *, strip_headers: bool = True) -> list:
    """Strip noise from Pandoc AST block list.

    * Removes ``data-pos`` and ``data-source-file`` key-value pairs from
      every Attr triple.
    * Optionally removes Header blocks (the decompiler renders its own).
    * Unwraps trivial Div wrappers (Div with no id/classes/attrs).
    * Strips DefinitionList / BlockQuote blocks (CommonSpec attribute syntax).
    * Strips standalone relation-link paragraphs (``[target](@)``).
    """
    cleaned = _strip_kv_attrs(blocks)
    if not isinstance(cleaned, list):
        return cleaned

    # Flatten: unwrap trivial Divs recursively
    flat = _unwrap_trivial_divs(cleaned)

    result = []
    for block in flat:
        if not isinstance(block, dict):
            continue
        t = block.get("t")
        if strip_headers and t == "Header":
            continue
        # DefinitionList = CommonSpec attribute definitions
        if t == "DefinitionList":
            continue
        # BlockQuote = CommonSpec `> name: value` attribute syntax
        if t == "BlockQuote":
            continue
        # Para with only relation links: [target](@) or [target](#)
        if t == "Para" and _is_relation_para(block):
            continue
        result.append(block)
    return result


# Structural Div classes injected by SpecCompiler's Pandoc filter.
# These are always safe to unwrap (they're presentation wrappers).
_STRUCTURAL_CLASSES = frozenset({
    "spec-object", "spec-object-header", "spec-object-body",
    "spec-object-attributes", "spec-object-relations",
})


def _should_unwrap_div(block: dict) -> bool:
    """Check if a Div block should be unwrapped (is trivial/structural)."""
    attr = block.get("c", [None])[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return False
    ident, classes, kvs = attr[0], attr[1], attr[2]
    # Trivial: no id, no classes, no KVs
    if not ident and not classes and not kvs:
        return True
    # Structural: has a well-known class, no meaningful id
    if (not ident
            and isinstance(classes, list)
            and any(c in _STRUCTURAL_CLASSES for c in classes)):
        return True
    return False


def _unwrap_trivial_divs(blocks: list) -> list:
    """Recursively unwrap Div wrappers that carry no semantic content.

    Operates throughout the entire block tree — including inside list items,
    block quotes, and other nested block containers.
    """
    result = []
    for block in blocks:
        if isinstance(block, dict) and block.get("t") == "Div":
            if _should_unwrap_div(block):
                inner = block["c"][1] if len(block["c"]) > 1 else []
                result.extend(_unwrap_trivial_divs(inner))
                continue
        # Recurse into block types that contain block lists
        result.append(_recurse_block_children(block))
    return result


def _recurse_block_children(block) -> dict:
    """Recursively unwrap trivial Divs inside a block's children."""
    if not isinstance(block, dict):
        return block
    t = block.get("t")
    c = block.get("c")
    if c is None:
        return block

    # OrderedList: c = [ListAttributes, [[Block]]]
    if t == "OrderedList" and isinstance(c, list) and len(c) == 2:
        items = c[1]
        new_items = [_unwrap_trivial_divs(item) for item in items]
        return {"t": t, "c": [c[0], new_items]}

    # BulletList: c = [[Block]]
    if t == "BulletList" and isinstance(c, list):
        new_items = [_unwrap_trivial_divs(item) for item in c]
        return {"t": t, "c": new_items}

    # BlockQuote: c = [Block]
    if t == "BlockQuote" and isinstance(c, list):
        return {"t": t, "c": _unwrap_trivial_divs(c)}

    # Div (non-trivial, we keep it): c = [Attr, [Block]]
    if t == "Div" and isinstance(c, list) and len(c) == 2:
        return {"t": t, "c": [c[0], _unwrap_trivial_divs(c[1])]}

    return block


def _is_relation_para(block: dict) -> bool:
    """Check if a Para block consists solely of a relation Link.

    CommonSpec relations are standalone paragraphs like ``[target](@)``
    or ``[target](#)``.
    """
    inlines = block.get("c", [])
    # Strip surrounding whitespace inlines
    stripped = [i for i in inlines if isinstance(i, dict) and i.get("t") not in ("Space", "SoftBreak")]
    if len(stripped) != 1:
        return False
    link = stripped[0]
    if not isinstance(link, dict) or link.get("t") != "Link":
        return False
    # Link.c = [Attr, [Inlines], [url, title]]
    target = link.get("c", [None, None, [""]])[2]
    if isinstance(target, list) and len(target) >= 1:
        url = target[0]
        return url in ("@", "#")
    return False


def _merge_plain_blocks(blocks: list) -> list:
    """Merge consecutive Plain blocks into a single Plain.

    SpecCompiler's Lua pipeline stores each inline element as a separate
    Plain block in attribute ASTs.  Pandoc renders each Plain on its own
    line, producing word-per-line output.  Merging fixes this.
    """
    result = []
    acc_inlines: list = []

    def flush():
        if acc_inlines:
            result.append({"t": "Plain", "c": list(acc_inlines)})
            acc_inlines.clear()

    for block in blocks:
        if isinstance(block, dict) and block.get("t") == "Plain":
            acc_inlines.extend(block.get("c", []))
        else:
            flush()
            result.append(block)
    flush()
    return result


def _strip_kv_attrs(node):
    """Recursively remove data-pos / data-source-file from Pandoc KV pairs."""
    if isinstance(node, dict):
        return {k: _strip_kv_attrs(v) for k, v in node.items()}
    if isinstance(node, list):
        out = []
        for item in node:
            # Pandoc KV pair: [key, value]  — skip noise keys
            if (isinstance(item, list) and len(item) == 2
                    and isinstance(item[0], str)
                    and item[0] in ("data-pos", "data-source-file")):
                continue
            out.append(_strip_kv_attrs(item))
        return out
    return node


# ── Pandoc subprocess ────────────────────────────────────────────────────

_PANDOC_API_VERSION = [1, 23, 1]


def _run_pandoc(input_text: str, from_fmt: str, to_fmt: str = "markdown") -> Optional[str]:
    """Run pandoc to convert *from_fmt* → *to_fmt*.  Returns None on failure."""
    pandoc = get_pandoc()
    if pandoc is None:
        return None
    try:
        result = subprocess.run(
            [pandoc, "-f", from_fmt, "-t", to_fmt, "--wrap=none"],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _post_clean(md: str) -> str:
    """Post-process Pandoc markdown output.

    * Strip trailing whitespace / excessive blank lines.
    * Remove residual empty ``<div>`` / ``</div>`` tags.
    """
    md = re.sub(r"<div>\s*</div>", "", md)
    md = re.sub(r"^\s*</?div>\s*$", "", md, flags=re.MULTILINE)
    # Collapse 3+ consecutive newlines → 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


# ── Public conversion functions ──────────────────────────────────────────

def ast_to_markdown(ast_json: str, *, strip_headers: bool = True) -> Optional[str]:
    """Convert a Pandoc AST JSON block list to CommonSpec Markdown.

    Parameters
    ----------
    ast_json : str
        JSON string containing a list of Pandoc Block elements
        (as stored in ``spec_objects.ast`` or ``spec_attribute_values.ast``).
    strip_headers : bool
        If *True* (default), Header blocks are removed — the decompiler
        renders its own headings from type/PID metadata.

    Returns
    -------
    str or None
        Markdown text, or *None* if conversion fails.
    """
    if not ast_json or not ast_json.strip():
        return None
    try:
        blocks = json.loads(ast_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(blocks, list) or not blocks:
        return None

    cleaned = _clean_ast_blocks(blocks, strip_headers=strip_headers)
    if not cleaned:
        return None

    # Merge fragmented Plain blocks (common in attribute ASTs).
    cleaned = _merge_plain_blocks(cleaned)

    doc = {
        "pandoc-api-version": _PANDOC_API_VERSION,
        "meta": {},
        "blocks": cleaned,
    }
    raw = _run_pandoc(json.dumps(doc), "json")
    if raw is None:
        return None
    return _post_clean(raw) or None


def _detect_input_format(text: str) -> str:
    """Detect whether *text* is HTML or plain/RST text.

    StrictDoc exports ReqIF content as plain text (often with RST directives)
    stored in STRING attributes, not XHTML.  If the content has no HTML tags
    we should tell Pandoc to read it as RST rather than HTML, otherwise the
    structure (code blocks, lists, paragraphs) is lost.
    """
    stripped = text.strip()
    # Quick check: does it look like it has any HTML tags?
    if re.search(r"<\s*[a-zA-Z][^>]*>", stripped):
        return "html"
    # Contains RST directives?
    if re.search(r"^\.\.\s+\w+", stripped, re.MULTILINE):
        return "rst"
    # Plain text with paragraph breaks — still better as RST than HTML.
    return "rst"


def html_to_markdown(html: str) -> Optional[str]:
    """Convert an HTML or plain-text fragment to Markdown via Pandoc.

    Parameters
    ----------
    html : str
        HTML5 fragment, RST text, or plain text (as stored in
        ``content_xhtml`` or ``xhtml_value``).

    Returns
    -------
    str or None
        Markdown text, or *None* if conversion fails.
    """
    if not html or not html.strip():
        return None
    fmt = _detect_input_format(html)
    raw = _run_pandoc(html, fmt)
    if raw is None:
        return None
    return _post_clean(raw) or None


def body_to_markdown(
    ast_json: Optional[str] = None,
    content_xhtml: Optional[str] = None,
) -> Optional[str]:
    """Convert body content to Markdown using the best available source.

    Fallback chain: ``ast`` → ``content_xhtml`` → *None*.
    """
    if ast_json:
        md = ast_to_markdown(ast_json, strip_headers=True)
        if md:
            return md
    if content_xhtml:
        md = html_to_markdown(content_xhtml)
        if md:
            return md
    return None


def attr_xhtml_to_markdown(
    ast_json: Optional[str] = None,
    xhtml_value: Optional[str] = None,
    string_value: Optional[str] = None,
) -> Optional[str]:
    """Convert an XHTML attribute value to Markdown.

    Fallback chain: ``ast`` → ``xhtml_value`` (HTML) → ``string_value`` (plain).
    """
    if ast_json:
        md = ast_to_markdown(ast_json, strip_headers=False)
        if md:
            return md
    if xhtml_value:
        md = html_to_markdown(xhtml_value)
        if md:
            return md
    return string_value or None


# ── HTML output (for ReqIF export) ───────────────────────────────────────

def ast_to_html(ast_json: str, *, strip_headers: bool = True) -> Optional[str]:
    """Convert a Pandoc AST JSON block list to HTML5 fragment.

    Used by the ReqIF exporter to populate ``ReqIF.Text`` when
    ``content_xhtml`` is empty (SpecCompiler-built databases store only
    the Pandoc AST, not pre-rendered HTML).

    Parameters
    ----------
    ast_json : str
        JSON string containing a list of Pandoc Block elements.
    strip_headers : bool
        If *True* (default), Header blocks are removed.

    Returns
    -------
    str or None
        HTML5 fragment, or *None* if conversion fails.
    """
    if not ast_json or not ast_json.strip():
        return None
    try:
        blocks = json.loads(ast_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(blocks, list) or not blocks:
        return None

    cleaned = _clean_ast_blocks(blocks, strip_headers=strip_headers)
    if not cleaned:
        return None

    cleaned = _merge_plain_blocks(cleaned)

    doc = {
        "pandoc-api-version": _PANDOC_API_VERSION,
        "meta": {},
        "blocks": cleaned,
    }
    raw = _run_pandoc(json.dumps(doc), "json", "html")
    if raw is None:
        return None
    return raw.strip() or None


def body_to_html(
    ast_json: Optional[str] = None,
    content_xhtml: Optional[str] = None,
) -> Optional[str]:
    """Convert body content to HTML5 using the best available source.

    Fallback chain: ``content_xhtml`` → ``ast`` (convert via Pandoc) → *None*.

    Note: prefers ``content_xhtml`` (already HTML) over AST conversion.
    """
    if content_xhtml and content_xhtml.strip():
        return content_xhtml.strip()
    if ast_json:
        return ast_to_html(ast_json, strip_headers=True)
    return None


def attr_xhtml_to_html(
    ast_json: Optional[str] = None,
    xhtml_value: Optional[str] = None,
    string_value: Optional[str] = None,
) -> Optional[str]:
    """Convert an XHTML attribute value to HTML5.

    Fallback chain: ``xhtml_value`` → ``ast`` (convert) → ``string_value``.
    """
    if xhtml_value and xhtml_value.strip():
        return xhtml_value.strip()
    if ast_json:
        html = ast_to_html(ast_json, strip_headers=False)
        if html:
            return html
    return string_value or None
