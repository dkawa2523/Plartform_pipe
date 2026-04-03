"""CSV/Parquet IO helpers (no ClearML dependency)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .schema import TabularSchema

__all__ = ["read_table", "write_table"]


def read_table(
    path: str | Path,
    schema: TabularSchema | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    path = Path(path)
    fmt = _infer_format(path)
    if _is_tsv(path):
        kwargs.setdefault("sep", "\t")
    if schema is not None:
        if fmt == "csv":
            kwargs.setdefault("usecols", schema.all_columns)
        elif fmt == "parquet":
            kwargs.setdefault("columns", schema.all_columns)
    if fmt == "csv":
        return pd.read_csv(path, **kwargs)
    if fmt == "parquet":
        return pd.read_parquet(path, **kwargs)
    raise ValueError(f"Unsupported format for {path}")


def write_table(
    frame: pd.DataFrame,
    path: str | Path,
    **kwargs: Any,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = _infer_format(path)
    if fmt == "csv":
        if _is_tsv(path):
            kwargs.setdefault("sep", "\t")
        kwargs.setdefault("index", False)
        frame.to_csv(path, **kwargs)
        return path
    if fmt == "parquet":
        kwargs.setdefault("index", False)
        frame.to_parquet(path, **kwargs)
        return path
    raise ValueError(f"Unsupported format for {path}")


def _infer_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv") or name.endswith(".csv.gz"):
        return "csv"
    if name.endswith(".tsv") or name.endswith(".tsv.gz"):
        return "csv"
    if name.endswith(".parquet") or name.endswith(".pq"):
        return "parquet"
    raise ValueError(f"Unknown file extension for {path}")


def _is_tsv(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".tsv") or name.endswith(".tsv.gz")
