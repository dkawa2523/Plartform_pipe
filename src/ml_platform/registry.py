"""Registry interfaces for models/metrics/preprocessors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

__all__ = [
    "MetricFn",
    "ModelFactory",
    "PreprocessorFactory",
    "PluginRegistry",
    "MODEL_REGISTRY",
    "METRIC_REGISTRY",
    "PREPROCESSOR_REGISTRY",
    "get_metric",
    "get_model",
    "get_preprocessor",
    "list_metrics",
    "list_models",
    "list_preprocessors",
    "register_metric",
    "register_model",
    "register_preprocessor",
]

T = TypeVar("T")

ModelFactory = Callable[..., Any]
MetricFn = Callable[..., Any]
PreprocessorFactory = Callable[..., Any]


@dataclass
class PluginRegistry(Generic[T]):
    kind: str
    _items: dict[str, T] = field(default_factory=dict)

    def register(self, name: str, item: T, *, allow_override: bool = False) -> None:
        if not name:
            raise ValueError(f"{self.kind} name is required")
        if not allow_override and name in self._items:
            raise KeyError(f"{self.kind} already registered: {name}")
        self._items[name] = item

    def get(self, name: str) -> T:
        try:
            return self._items[name]
        except KeyError:
            raise KeyError(f"{self.kind} not registered: {name}") from None

    def list(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


MODEL_REGISTRY = PluginRegistry[ModelFactory]("model")
METRIC_REGISTRY = PluginRegistry[MetricFn]("metric")
PREPROCESSOR_REGISTRY = PluginRegistry[PreprocessorFactory]("preprocessor")


def register_model(
    name: str,
    factory: ModelFactory,
    *,
    allow_override: bool = False,
    registry: PluginRegistry[ModelFactory] = MODEL_REGISTRY,
) -> None:
    registry.register(name, factory, allow_override=allow_override)


def register_metric(
    name: str,
    metric_fn: MetricFn,
    *,
    allow_override: bool = False,
    registry: PluginRegistry[MetricFn] = METRIC_REGISTRY,
) -> None:
    registry.register(name, metric_fn, allow_override=allow_override)


def register_preprocessor(
    name: str,
    factory: PreprocessorFactory,
    *,
    allow_override: bool = False,
    registry: PluginRegistry[PreprocessorFactory] = PREPROCESSOR_REGISTRY,
) -> None:
    registry.register(name, factory, allow_override=allow_override)


def get_model(
    name: str,
    *,
    registry: PluginRegistry[ModelFactory] = MODEL_REGISTRY,
) -> ModelFactory:
    return registry.get(name)


def get_metric(
    name: str,
    *,
    registry: PluginRegistry[MetricFn] = METRIC_REGISTRY,
) -> MetricFn:
    return registry.get(name)


def get_preprocessor(
    name: str,
    *,
    registry: PluginRegistry[PreprocessorFactory] = PREPROCESSOR_REGISTRY,
) -> PreprocessorFactory:
    return registry.get(name)


def list_models(*, registry: PluginRegistry[ModelFactory] = MODEL_REGISTRY) -> tuple[str, ...]:
    return registry.list()


def list_metrics(*, registry: PluginRegistry[MetricFn] = METRIC_REGISTRY) -> tuple[str, ...]:
    return registry.list()


def list_preprocessors(
    *,
    registry: PluginRegistry[PreprocessorFactory] = PREPROCESSOR_REGISTRY,
) -> tuple[str, ...]:
    return registry.list()
