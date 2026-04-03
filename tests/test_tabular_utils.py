from __future__ import annotations

import pandas as pd

from ml_platform.core.tabular.bundle import PreprocessBundle
from ml_platform.core.tabular.io import read_table, write_table
from ml_platform.core.tabular.schema import TabularSchema


class _DoubleTransformer:
    def __init__(self) -> None:
        self.fitted = False

    def fit(self, data, target=None):  # noqa: ANN001, ANN201
        self.fitted = True

    def transform(self, data):  # noqa: ANN001, ANN201
        return data * 2


def test_read_write_table_csv(tmp_path) -> None:
    frame = pd.DataFrame({"id": [1, 2], "x": [0.1, 0.2], "y": [1, 0]})
    path = tmp_path / "data.csv"
    write_table(frame, path)

    schema = TabularSchema(features=["x"], target="y", id_columns=["id"])
    loaded = read_table(path, schema=schema)
    assert list(loaded.columns) == ["id", "x", "y"]
    assert loaded.shape == (2, 3)


def test_preprocess_bundle_fit_transform() -> None:
    frame = pd.DataFrame({"id": [1, 2], "f1": [1, 2], "y": [10, 20]})
    schema = TabularSchema(features=["f1"], target="y", id_columns=["id"])
    bundle = PreprocessBundle(
        schema,
        feature_transformer=_DoubleTransformer(),
        target_transformer=_DoubleTransformer(),
    )

    batch = bundle.fit_transform(frame)
    assert bundle.feature_transformer.fitted is True
    assert bundle.target_transformer.fitted is True
    assert batch.features["f1"].tolist() == [2, 4]
    assert batch.target.tolist() == [20, 40]
    assert batch.ids["id"].tolist() == [1, 2]
