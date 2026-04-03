"""Tabular schema utilities (no ClearML dependency)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

__all__ = ["TabularSchema", "load_schema_json", "save_schema_json"]


@dataclass(frozen=True)
class TabularSchema:
    features: list[str]
    target: str | None = None
    id_columns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        features = list(self.features) if self.features is not None else []
        id_columns = list(self.id_columns) if self.id_columns is not None else []
        target = self.target
        object.__setattr__(self, "features", features)
        object.__setattr__(self, "id_columns", id_columns)
        object.__setattr__(self, "target", target)
        _ensure_unique("features", features)
        _ensure_unique("id_columns", id_columns)
        overlap = set(features) & set(id_columns)
        if target is not None and (target in features or target in id_columns):
            raise ValueError("target must not overlap with id_columns/features")
        if overlap:
            raise ValueError("features and id_columns must be disjoint")

    @property
    def all_columns(self) -> list[str]:
        columns = list(self.id_columns) + list(self.features)
        if self.target:
            columns.append(self.target)
        return columns

    def to_dict(self) -> dict[str, object]:
        return {
            "features": list(self.features),
            "target": self.target,
            "id_columns": list(self.id_columns),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "TabularSchema":
        features = list(payload.get("features") or [])
        target = payload.get("target")
        id_columns = list(payload.get("id_columns") or [])
        return cls(features=features, target=target, id_columns=id_columns)

    def validate_columns(self, columns: Iterable[str]) -> None:
        column_set = set(columns)
        missing = [name for name in self.all_columns if name not in column_set]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def to_json(self, path: str | Path) -> Path:
        return save_schema_json(self, path)

    @classmethod
    def from_json(cls, path: str | Path) -> "TabularSchema":
        return load_schema_json(path)


def load_schema_json(path: str | Path) -> TabularSchema:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, Mapping):
        raise ValueError("Schema JSON must be a JSON object")
    return TabularSchema.from_dict(payload)


def save_schema_json(schema: TabularSchema, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(schema.to_dict(), file, indent=2, ensure_ascii=True)
    return path


def _ensure_unique(name: str, columns: Sequence[str]) -> None:
    seen: set[str] = set()
    duplicates = [col for col in columns if col in seen or seen.add(col)]
    if duplicates:
        raise ValueError(f"{name} contains duplicates: {duplicates}")
