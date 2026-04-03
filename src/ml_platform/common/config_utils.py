"""Shared config selection helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

_OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError)
_OMEGACONF_RECOVERABLE_ERRORS = (
    AttributeError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)


def cfg_value(cfg: Any, dotted_path: str, default: Any | None = None) -> Any:
    if cfg is None:
        return default
    try:
        from omegaconf import OmegaConf  # type: ignore
    except (AttributeError, ImportError, ModuleNotFoundError, RuntimeError, TypeError, ValueError):
        OmegaConf = None
    if OmegaConf is not None:
        try:
            value = OmegaConf.select(cfg, dotted_path)
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            value = None
        if value is not None:
            return value
    current = cfg
    for key in dotted_path.split("."):
        if isinstance(current, Mapping):
            if key not in current:
                return default
            current = current[key]
            continue
        if not hasattr(current, key):
            return default
        current = getattr(current, key)
    return default if current is None else current


def _cfg_value(cfg: Any, dotted_path: str, default: Any | None = None) -> Any:
    return cfg_value(cfg, dotted_path, default=default)


def to_container(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    try:
        from omegaconf import OmegaConf  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS:
        OmegaConf = None
    if OmegaConf is not None:
        try:
            if OmegaConf.is_config(value):
                return OmegaConf.to_container(value, resolve=True, throw_on_missing=False)
        except _OMEGACONF_RECOVERABLE_ERRORS:
            pass
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return value


def _to_container(value: Any) -> Any:
    return to_container(value)


__all__ = ["cfg_value", "_cfg_value", "to_container", "_to_container"]
