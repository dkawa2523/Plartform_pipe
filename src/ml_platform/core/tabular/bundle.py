"""Preprocessing bundle for tabular data (no ClearML dependency)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .schema import TabularSchema

__all__ = ["TabularBatch", "PreprocessBundle"]


@dataclass
class TabularBatch:
    features: Any
    target: Any | None
    ids: pd.DataFrame | None


class PreprocessBundle:
    def __init__(
        self,
        schema: TabularSchema,
        feature_transformer: Any | None = None,
        target_transformer: Any | None = None,
    ) -> None:
        self.schema = schema
        self.feature_transformer = feature_transformer
        self.target_transformer = target_transformer

    def fit(self, frame: pd.DataFrame) -> "PreprocessBundle":
        self._validate_frame(frame)
        features, target = self._split(frame)
        _call_fit(self.feature_transformer, features, target)
        if target is not None:
            _call_fit(self.target_transformer, target)
        return self

    def transform(self, frame: pd.DataFrame) -> TabularBatch:
        self._validate_frame(frame)
        features, target = self._split(frame)
        ids = self._extract_ids(frame)
        features = _call_transform(self.feature_transformer, features)
        if target is not None:
            target = _call_transform(self.target_transformer, target)
        return TabularBatch(features=features, target=target, ids=ids)

    def fit_transform(self, frame: pd.DataFrame) -> TabularBatch:
        self.fit(frame)
        return self.transform(frame)

    def inverse_transform(self, target: Any) -> Any:
        return _call_inverse_transform(self.target_transformer, target)

    def serialize(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def deserialize(cls, path: str | Path) -> "PreprocessBundle":
        return joblib.load(path)

    def _split(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, Any | None]:
        features = frame[self.schema.features]
        if self.schema.target:
            return features, frame[self.schema.target]
        return features, None

    def _extract_ids(self, frame: pd.DataFrame) -> pd.DataFrame | None:
        if not self.schema.id_columns:
            return None
        return frame[self.schema.id_columns]

    def _validate_frame(self, frame: pd.DataFrame) -> None:
        columns = getattr(frame, "columns", None)
        if columns is None:
            raise ValueError("Frame must have columns")
        self.schema.validate_columns(columns)


def _call_fit(transformer: Any | None, data: Any, target: Any | None = None) -> None:
    if transformer is None:
        return
    fit = getattr(transformer, "fit", None)
    if not callable(fit):
        return
    try:
        fit(data, target)
    except TypeError:
        fit(data)


def _call_transform(transformer: Any | None, data: Any) -> Any:
    if transformer is None:
        return data
    transform = getattr(transformer, "transform", None)
    if not callable(transform):
        return data
    return transform(data)


def _call_inverse_transform(transformer: Any | None, data: Any) -> Any:
    if transformer is None:
        return data
    inverse = getattr(transformer, "inverse_transform", None)
    if not callable(inverse):
        return data
    return inverse(data)
