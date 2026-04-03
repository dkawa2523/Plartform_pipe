from __future__ import annotations

import pytest

from ml_platform.registry import PluginRegistry, get_model, list_models, register_model


def test_registry_register_get_list() -> None:
    registry = PluginRegistry("model")

    def factory() -> str:
        return "ok"

    register_model("linear", factory, registry=registry)
    assert get_model("linear", registry=registry) is factory
    assert list_models(registry=registry) == ("linear",)


def test_registry_duplicate_and_missing() -> None:
    registry = PluginRegistry("metric")
    registry.register("acc", lambda: 1)
    with pytest.raises(KeyError):
        registry.register("acc", lambda: 2)
    with pytest.raises(KeyError):
        registry.get("missing")
