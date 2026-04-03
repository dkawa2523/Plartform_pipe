"""Deterministic hashing helpers for configs/splits/recipes."""

from __future__ import annotations

from ..common.config_utils import to_container as _to_container
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

__all__ = ["hash_config", "hash_split", "hash_recipe"]


def hash_config(config: Any) -> str:
    return _hash_payload(config)


def hash_split(split: Any) -> str:
    return _hash_payload(split)


def hash_recipe(recipe: Any) -> str:
    return _hash_payload(recipe)


def _hash_payload(payload: Any) -> str:
    normalized = _normalize(payload)
    encoded = _stable_dumps(normalized).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize(value: Any) -> Any:
    value = _to_container(value)
    if isinstance(value, Mapping):
        items = sorted(value.items(), key=lambda item: str(item[0]))
        return {str(key): _normalize(val) for key, val in items}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, set):
        normalized = [_normalize(item) for item in value]
        return sorted(normalized, key=_stable_dumps)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _stable_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
