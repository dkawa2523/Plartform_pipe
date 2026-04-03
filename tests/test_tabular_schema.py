from __future__ import annotations

import pytest

from ml_platform.core.tabular.schema import TabularSchema


def test_schema_columns_and_validation() -> None:
    schema = TabularSchema(features=["f1", "f2"], target="y", id_columns=["id"])
    assert schema.all_columns == ["id", "f1", "f2", "y"]
    schema.validate_columns(["id", "f1", "f2", "y", "extra"])


def test_schema_rejects_overlap_and_duplicates() -> None:
    with pytest.raises(ValueError):
        TabularSchema(features=["dup", "dup"])
    with pytest.raises(ValueError):
        TabularSchema(features=["x"], id_columns=["x"])
    with pytest.raises(ValueError):
        TabularSchema(features=["x"], target="x")
