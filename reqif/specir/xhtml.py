"""XHTML namespace conversion helpers for ReqIF ↔ SpecIR.

SpecIR stores HTML5 fragments (no namespace prefix) in
``spec_objects.content_xhtml`` and ``spec_attribute_values.xhtml_value``.
ReqIF uses ``reqif-xhtml:`` (or ``xhtml:``) namespace-prefixed XHTML.

This module bridges the two representations.
"""
from __future__ import annotations

import re

from reqif.helpers.lxml import (
    lxml_convert_to_reqif_ns_xhtml_string,
)


def to_reqif_xhtml(html5_fragment: str) -> str:
    """Convert an HTML5 fragment to ReqIF XHTML (``xhtml:`` namespace).

    Wraps in ``<div>`` if the fragment is not already a single root element,
    then applies namespace conversion via the reqif helper.
    """
    fragment = (html5_fragment or "").strip()
    if not fragment:
        fragment = "<div></div>"
    else:
        fragment = f"<div>{fragment}</div>"
    return lxml_convert_to_reqif_ns_xhtml_string(fragment, reqif_xhtml=False)


_NS_PREFIX_RE = re.compile(r"<(/?)(?:reqif-xhtml|xhtml):", re.IGNORECASE)


def from_reqif_xhtml(reqif_xhtml_str: str) -> str:
    """Convert ReqIF XHTML (namespace-prefixed) back to plain HTML5.

    Strips ``reqif-xhtml:`` / ``xhtml:`` prefixes and unwraps the outer
    ``<div>`` wrapper if present.
    """
    if not reqif_xhtml_str:
        return ""
    # Strip namespace prefixes
    html = _NS_PREFIX_RE.sub(r"<\1", reqif_xhtml_str)
    # Strip xmlns declarations
    html = re.sub(r'\s+xmlns(?::[a-zA-Z-]+)?="[^"]*"', "", html)
    # Unwrap outer <div>...</div> if it's the only root element
    html = html.strip()
    if html.lower().startswith("<div>") and html.lower().endswith("</div>"):
        inner = html[5:-6].strip()
        if inner:
            return inner
    return html
