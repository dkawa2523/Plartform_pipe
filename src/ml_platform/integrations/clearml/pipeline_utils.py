"""ClearML pipeline utilities (parameter handoff + manifests)."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping

from ml_platform.common.config_utils import cfg_value as _cfg_value
from ml_platform.config import resolve_output_dir
from ml_platform.integrations.clearml import apply_task_script, is_clearml_enabled, upload_artifact

PIPELINE_STEP_TASK_IDS_NAME = "step_task_ids.json"
PIPELINE_PARAM_PREFIX = "pipeline"
FIXED_REUSE_LAST_TASK_ID = False
_OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError)

__all__ = [
    "FIXED_REUSE_LAST_TASK_ID",
    "PIPELINE_PARAM_PREFIX",
    "PIPELINE_STEP_TASK_IDS_NAME",
    "build_step_task_ids",
    "create_controller",
    "fixed_reuse_last_task_id",
    "handoff_dataset_id",
    "handoff_model_id",
    "handoff_step_artifact",
    "handoff_step_task_id",
    "merge_param_overrides",
    "maybe_create_controller",
    "pipeline_param_ref",
    "require_clearml_agent",
    "step_artifact_ref",
    "step_task_id_ref",
    "write_step_task_ids",
]


def fixed_reuse_last_task_id() -> bool:
    return FIXED_REUSE_LAST_TASK_ID


def pipeline_param_ref(name: str) -> str:
    return f"${{{PIPELINE_PARAM_PREFIX}.{name}}}"


def step_task_id_ref(step_name: str) -> str:
    return f"${{{step_name}.id}}"


def step_artifact_ref(step_name: str, artifact_name: str) -> str:
    return f"${{{step_name}.artifacts.{artifact_name}}}"


def handoff_dataset_id(param_name: str = "dataset_id", key: str = "data.dataset_id") -> dict[str, str]:
    return {key: pipeline_param_ref(param_name)}


def handoff_model_id(param_name: str = "model_id", key: str = "task.model_id") -> dict[str, str]:
    return {key: pipeline_param_ref(param_name)}


def handoff_step_task_id(step_name: str, key: str) -> dict[str, str]:
    return {key: step_task_id_ref(step_name)}


def handoff_step_artifact(step_name: str, artifact_name: str, key: str) -> dict[str, str]:
    return {key: step_artifact_ref(step_name, artifact_name)}


def merge_param_overrides(*overrides: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for override in overrides:
        merged.update(dict(override))
    return merged


def build_step_task_ids(steps: Mapping[str, Any] | Iterable[Any]) -> dict[str, str]:
    if isinstance(steps, Mapping):
        items = steps.items()
    else:
        items = ((_step_name(step), step) for step in steps)
    payload: dict[str, str] = {}
    for name, step in items:
        if not name:
            continue
        task_id = _coerce_task_id(step)
        if task_id:
            payload[str(name)] = task_id
    return payload


def write_step_task_ids(
    steps: Mapping[str, Any] | Iterable[Any],
    *,
    output_dir: str | Path | None = None,
    cfg: Any | None = None,
    task: Any | None = None,
    filename: str = PIPELINE_STEP_TASK_IDS_NAME,
) -> Path:
    payload = build_step_task_ids(steps)
    output_base = _resolve_output_dir(cfg, output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    path = output_base / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
    if task is not None:
        upload_artifact(task, filename, path)
    return path


def create_controller(
    cfg: Any,
    *,
    name: str | None = None,
    project: str | None = None,
    version: str | None = None,
    tags: Iterable[str] | None = None,
    default_queue: str | None = None,
) -> Any:
    if not is_clearml_enabled(cfg):
        raise RuntimeError("ClearML is disabled. Set run.clearml.enabled=true to use PipelineController.")
    controller = _init_controller(cfg, name=name, project=project, version=version)
    _maybe_add_tags(controller, tags)
    _maybe_set_default_queue(controller, default_queue or _cfg_value(cfg, "run.clearml.queue_name"))
    _maybe_apply_task_script(controller, cfg)
    return controller


def maybe_create_controller(
    cfg: Any,
    *,
    name: str | None = None,
    project: str | None = None,
    version: str | None = None,
    tags: Iterable[str] | None = None,
    default_queue: str | None = None,
) -> Any | None:
    if not is_clearml_enabled(cfg):
        return None
    return create_controller(
        cfg,
        name=name,
        project=project,
        version=version,
        tags=tags,
        default_queue=default_queue,
    )


def require_clearml_agent(queue_name: str | None = None) -> None:
    if queue_name is None:
        return
    if shutil.which("clearml-agent") is None:
        raise RuntimeError(
            "clearml-agent not found. Install it or disable remote execution "
            f"(queue={queue_name})."
        )


def _init_controller(cfg: Any, name: str | None, project: str | None, version: str | None) -> Any:
    controller_cls = _load_pipeline_controller()
    controller_name = name or _cfg_value(cfg, "run.clearml.task_name") or "pipeline"
    project_name = project or _cfg_value(cfg, "run.clearml.project_name") or "default"
    return controller_cls(name=controller_name, project=project_name, version=version)


def _load_pipeline_controller() -> Any:
    try:
        from clearml import PipelineController  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS:
        try:
            from clearml.automation.controller import PipelineController  # type: ignore
        except _OPTIONAL_IMPORT_ERRORS as exc:
            raise RuntimeError(
                "ClearML PipelineController is not available. Install clearml or disable run.clearml.enabled."
            ) from exc
    return PipelineController


def _maybe_apply_task_script(controller: Any, cfg: Any) -> bool:
    task = _pipeline_task(controller) or controller
    return apply_task_script(task, cfg)


def _maybe_set_default_queue(controller: Any, queue_name: str | None) -> bool:
    if not queue_name:
        return False
    setter = getattr(controller, "set_default_execution_queue", None)
    if callable(setter):
        setter(queue_name)
        return True
    return False


def _maybe_add_tags(controller: Any, tags: Iterable[str] | None) -> bool:
    if not tags:
        return False
    target = _pipeline_task(controller) or controller
    adder = getattr(target, "add_tags", None)
    if callable(adder):
        adder(list(tags))
        return True
    return False


def _pipeline_task(controller: Any) -> Any | None:
    for name in ("task", "_task", "pipeline_task"):
        if hasattr(controller, name):
            value = getattr(controller, name)
            if value is not None:
                return value
    return None


def _coerce_task_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("task_id", "id"):
            selected = value.get(key)
            if selected:
                return str(selected)
        if "task" in value:
            return _coerce_task_id(value["task"])
    for attr in ("task_id", "id", "task"):
        if hasattr(value, attr):
            selected = getattr(value, attr)
            if selected:
                return _coerce_task_id(selected)
    return None


def _step_name(step: Any) -> str | None:
    for attr in ("name", "step_name"):
        if hasattr(step, attr):
            selected = getattr(step, attr)
            if selected:
                return str(selected)
    if isinstance(step, Mapping):
        for key in ("name", "step_name"):
            selected = step.get(key)
            if selected:
                return str(selected)
    return None


def _resolve_output_dir(cfg: Any | None, output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    if cfg is not None:
        return resolve_output_dir(cfg, ".")
    return Path(".")
