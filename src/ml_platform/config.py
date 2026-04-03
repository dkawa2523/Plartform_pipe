"""Hydra config helpers and ClearML artifact export."""

from __future__ import annotations

from .common.config_utils import cfg_value as _cfg_value, to_container as _to_container
import json
from pathlib import Path
from typing import Any

__all__ = [
    "COMMON_GROUPS",
    "TASK_ROOTS",
    "TASK_ROOT_DEFAULTS",
    "export_config_artifact",
    "resolve_output_dir",
    "task_root_defaults",
]

TASK_ROOTS = ("preprocess", "train", "infer", "pipeline")
COMMON_GROUPS = ("run", "seed", "data", "eval")
_OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError)
_OMEGACONF_RECOVERABLE_ERRORS = (
    AttributeError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)

TASK_ROOT_DEFAULTS: dict[str, list[Any]] = {
    "preprocess": [
        "_self_",
        {"run": "base"},
        {"seed": "base"},
        {"data": "base"},
        {"eval": "base"},
        {"task": "preprocess/base"},
    ],
    "train": [
        "_self_",
        {"run": "base"},
        {"seed": "base"},
        {"data": "base"},
        {"eval": "base"},
        {"task": "train/base"},
    ],
    "infer": [
        "_self_",
        {"run": "base"},
        {"seed": "base"},
        {"data": "base"},
        {"eval": "base"},
        {"task": "infer/base"},
    ],
    "pipeline": [
        "_self_",
        {"run": "base"},
        {"seed": "base"},
        {"data": "base"},
        {"eval": "base"},
        {"task": "pipeline/base"},
    ],
}


def task_root_defaults(task_root: str) -> list[Any]:
    defaults = TASK_ROOT_DEFAULTS.get(task_root)
    if defaults is None:
        raise ValueError(f"Unknown task root: {task_root!r}")
    return list(defaults)


def export_config_artifact(
    cfg: Any,
    output_dir: str | Path | None = None,
    task: Any | None = None,
    artifact_name: str = "config_full.yaml",
) -> Path:
    """Write full config to config_full.yaml and optionally upload to ClearML."""
    output_base = Path(output_dir) if output_dir is not None else resolve_output_dir(cfg, ".")
    path = output_base / artifact_name
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_config_yaml(cfg, path)
    if task is not None:
        _upload_artifact(task, artifact_name, path)
    return path


def resolve_output_dir(cfg: Any, fallback: str | Path = ".") -> Path:
    output_dir = _cfg_value(cfg, "hydra.runtime.output_dir")
    if output_dir is None:
        output_dir = _cfg_value(cfg, "hydra.run.dir")
    if output_dir is None:
        output_dir = fallback
    return Path(output_dir)


def _write_config_yaml(cfg: Any, path: Path) -> None:
    if _save_omegaconf(cfg, path):
        return
    container = _to_container(cfg)
    if _save_yaml(container, path):
        return
    _save_json(container, path)


def _save_omegaconf(cfg: Any, path: Path) -> bool:
    try:
        from omegaconf import OmegaConf  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS:
        return False
    try:
        OmegaConf.save(cfg, path)
        return True
    except _OMEGACONF_RECOVERABLE_ERRORS:
        return False


def _save_yaml(container: Any, path: Path) -> bool:
    try:
        import yaml  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS:
        return False
    with path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(container, file, sort_keys=False, allow_unicode=False)
    return True


def _save_json(container: Any, path: Path) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(container, file, indent=2, ensure_ascii=True)


def _upload_artifact(task: Any, name: str, path: Path) -> None:
    uploader = getattr(task, "upload_artifact", None)
    if callable(uploader):
        uploader(name=name, artifact_object=str(path))
