"""Local import shim for src layout."""

from __future__ import annotations

from pathlib import Path

__all__ = []

_src_pkg = Path(__file__).resolve().parent.parent / "src" / "ml_platform"
if _src_pkg.is_dir():
    src_str = str(_src_pkg)
    if src_str not in __path__:
        __path__.append(src_str)
