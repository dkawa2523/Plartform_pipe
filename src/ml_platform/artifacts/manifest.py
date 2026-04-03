"""Manifest builders and writers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from ml_platform.config import resolve_output_dir
from ml_platform.integrations.clearml import upload_artifact

__all__ = ["build_manifest", "write_manifest"]

_REQUIRED_KEYS = ("schema_version", "code_version", "platform_version", "inputs", "outputs", "hashes")
_REQUIRED_HASH_KEYS = ("config_hash", "split_hash", "recipe_hash")


def build_manifest(
    *,
    schema_version: str,
    code_version: str,
    platform_version: str,
    inputs: Mapping[str, Any],
    outputs: Mapping[str, Any],
    hashes: Mapping[str, Any],
    **extras: Any,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": schema_version,
        "code_version": code_version,
        "platform_version": platform_version,
        "inputs": _coerce_mapping("inputs", inputs),
        "outputs": _coerce_mapping("outputs", outputs),
        "hashes": _coerce_mapping("hashes", hashes),
    }
    if extras:
        manifest.update(extras)
    _validate_manifest(manifest)
    return manifest


def write_manifest(
    manifest: Mapping[str, Any],
    *,
    output_dir: str | Path | None = None,
    cfg: Any | None = None,
    task: Any | None = None,
    filename: str = "manifest.json",
) -> Path:
    payload = _coerce_mapping("manifest", manifest)
    _validate_manifest(payload)
    output_base = _resolve_output_dir(cfg, output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    path = output_base / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
    if task is not None:
        upload_artifact(task, filename, path)
    return path


def _resolve_output_dir(cfg: Any | None, output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    if cfg is not None:
        return resolve_output_dir(cfg, ".")
    return Path(".")


def _coerce_mapping(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        raise ValueError(f"{name} is required")
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    raise ValueError(f"{name} must be a mapping")


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    missing = [key for key in _REQUIRED_KEYS if key not in manifest or manifest[key] is None]
    if missing:
        raise ValueError(f"manifest missing required keys: {', '.join(sorted(missing))}")
    hashes = manifest.get("hashes")
    if not isinstance(hashes, Mapping):
        raise ValueError("manifest 'hashes' must be a mapping")
    missing_hashes = [key for key in _REQUIRED_HASH_KEYS if key not in hashes or hashes[key] is None]
    if missing_hashes:
        raise ValueError(f"manifest missing hash keys: {', '.join(sorted(missing_hashes))}")
