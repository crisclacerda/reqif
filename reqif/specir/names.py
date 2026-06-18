"""Naming helpers for generated SpecIR/CommonSpec artifacts."""
from __future__ import annotations

import re


def to_commonspec_identifier(name: str) -> str:
    """Return a SpecCompiler-safe identifier for generated attribute names."""
    safe = re.sub(r"\W+", "_", name or "").strip("_")
    if not safe:
        return "attr"
    if safe[0].isdigit():
        return f"attr_{safe}"
    return safe
