"""ClearML integration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from ml_platform.common.config_utils import cfg_value as _cfg_value
from ml_platform.config import export_config_artifact
from ml_platform.versioning import get_code_version, get_platform_version, get_schema_version

__all__ = [
    "NoOpTask",
    "apply_task_script",
    "apply_ui_hygiene",
    "connect_hparams",
    "is_clearml_enabled",
    "maybe_execute_remotely",
    "report_plotly",
    "report_scalar",
    "report_table",
    "set_user_properties",
    "task_factory",
    "upload_artifact",
]
_OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError)
_RECOVERABLE_ERRORS = (AttributeError, OSError, RuntimeError, TypeError, ValueError)


class _NoOpLogger:
    def report_table(self, *args: Any, **kwargs: Any) -> None:
        return None

    def report_plotly(self, *args: Any, **kwargs: Any) -> None:
        return None

    def report_scalar(self, *args: Any, **kwargs: Any) -> None:
        return None

    def report_image(self, *args: Any, **kwargs: Any) -> None:
        return None

    def report_histogram(self, *args: Any, **kwargs: Any) -> None:
        return None


_NOOP_LOGGER = _NoOpLogger()


class NoOpTask:
    def __init__(self) -> None:
        self.is_enabled = False
        self.id = None

    def connect(self, configuration: Any = None, **kwargs: Any) -> Any:
        return configuration

    def set_user_properties(self, *args: Any, **kwargs: Any) -> None:
        return None

    def upload_artifact(self, *args: Any, **kwargs: Any) -> None:
        return None

    def get_logger(self) -> _NoOpLogger:
        return _NOOP_LOGGER

    def set_script(self, *args: Any, **kwargs: Any) -> None:
        return None

    def execute_remotely(self, *args: Any, **kwargs: Any) -> None:
        return None

    def add_tags(self, *args: Any, **kwargs: Any) -> None:
        return None


def is_clearml_enabled(cfg: Any) -> bool:
    return bool(_cfg_value(cfg, "run.clearml.enabled", False))


def task_factory(
    cfg: Any,
    *,
    task_type: Any | None = None,
    tags: Iterable[str] | None = None,
    reuse_last_task_id: str | None = None,
) -> Any:
    if not is_clearml_enabled(cfg):
        task = NoOpTask()
    else:
        task_cls = _load_clearml_task()
        project_name = _cfg_value(cfg, "run.clearml.project_name") or "default"
        task_name = _cfg_value(cfg, "run.clearml.task_name") or "task"
        try:
            task = task_cls.init(
                project_name=project_name,
                task_name=task_name,
                task_type=task_type,
                reuse_last_task_id=reuse_last_task_id,
                auto_connect_frameworks=False,
                auto_connect_arg_parser=False,
                auto_connect_streams=False,
            )
        except TypeError:
            task = task_cls.init(
                project_name=project_name,
                task_name=task_name,
                task_type=task_type,
                reuse_last_task_id=reuse_last_task_id,
                auto_connect_frameworks=False,
            )
    if tags:
        task.add_tags(list(tags))
    _apply_version_properties(task, cfg)
    apply_task_script(task, cfg)
    maybe_execute_remotely(task, cfg)
    return task


def connect_hparams(task: Any, hparams: Mapping[str, Any] | None, name: str = "HyperParameters") -> None:
    if not hparams:
        return
    task = _coerce_task(task)
    connector = getattr(task, "connect", None)
    if callable(connector):
        try:
            connector(hparams, name=name)
        except TypeError:
            connector(hparams)


def set_user_properties(task: Any, properties: Mapping[str, Any] | None) -> None:
    if not properties:
        return
    task = _coerce_task(task)
    setter = getattr(task, "set_user_properties", None)
    if callable(setter):
        normalized = {str(key): "" if value is None else str(value) for key, value in properties.items()}
        setter(**normalized)


def _apply_version_properties(task: Any, cfg: Any) -> None:
    version_props = {
        "platform_version": get_platform_version(),
        "code_version": get_code_version(repo_root=Path.cwd()),
        "schema_version": get_schema_version(cfg),
    }
    existing: Mapping[str, Any] | None = None
    getter = getattr(task, "get_user_properties", None)
    if callable(getter):
        try:
            existing = getter()
        except _RECOVERABLE_ERRORS:
            existing = None
    merged: dict[str, Any] = dict(existing) if isinstance(existing, Mapping) else {}
    # Keep existing user properties; only fill missing version keys.
    for key, value in version_props.items():
        merged.setdefault(key, value)
    set_user_properties(task, merged)


def upload_artifact(task: Any, name: str, artifact: Any) -> None:
    task = _coerce_task(task)
    uploader = getattr(task, "upload_artifact", None)
    if callable(uploader):
        if isinstance(artifact, Path):
            artifact = str(artifact)
        uploader(name=name, artifact_object=artifact)


def report_table(
    task: Any,
    title: str,
    series: str,
    *,
    iteration: int = 0,
    table: Any | None = None,
    csv: str | None = None,
) -> None:
    logger = _get_logger(task)
    reporter = getattr(logger, "report_table", None)
    if callable(reporter):
        try:
            reporter(title=title, series=series, iteration=iteration, table_plot=table, csv=csv)
        except TypeError:
            reporter(title, series, iteration, table, csv)


def report_plotly(
    task: Any,
    title: str,
    series: str,
    plot: Any,
    *,
    iteration: int = 0,
) -> None:
    logger = _get_logger(task)
    reporter = getattr(logger, "report_plotly", None)
    if callable(reporter):
        try:
            reporter(title=title, series=series, iteration=iteration, figure=plot)
        except TypeError:
            reporter(title, series, iteration, plot)


def report_scalar(
    task: Any,
    title: str,
    series: str,
    value: float,
    *,
    iteration: int = 0,
) -> None:
    logger = _get_logger(task)
    reporter = getattr(logger, "report_scalar", None)
    if callable(reporter):
        try:
            reporter(title=title, series=series, iteration=iteration, value=value)
        except TypeError:
            reporter(title, series, value, iteration)


def apply_ui_hygiene(
    task: Any,
    cfg: Any,
    *,
    hparams: Mapping[str, Any] | None = None,
    properties: Mapping[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> None:
    task = _coerce_task(task)
    connect_hparams(task, hparams)
    set_user_properties(task, properties)
    if cfg is not None:
        export_config_artifact(cfg, output_dir=output_dir, task=task)


def apply_task_script(task: Any, cfg: Any) -> bool:
    repository = _cfg_value(cfg, "run.clearml.ui_clone.repository")
    entry_point = _cfg_value(cfg, "run.clearml.ui_clone.entry_point")
    branch = _cfg_value(cfg, "run.clearml.ui_clone.branch")
    if not repository or not entry_point:
        return False
    task = _coerce_task(task)
    setter = getattr(task, "set_script", None)
    if callable(setter):
        payload = {"repository": repository, "entry_point": entry_point}
        if branch:
            payload["branch"] = branch
        setter(**payload)
        return True
    return False


def maybe_execute_remotely(task: Any, cfg: Any) -> bool:
    if not _cfg_value(cfg, "run.clearml.enqueue", False):
        return False
    task = _coerce_task(task)
    executor = getattr(task, "execute_remotely", None)
    if not callable(executor):
        return False
    queue_name = _cfg_value(cfg, "run.clearml.queue_name") or "default"
    executor(queue_name=queue_name)
    return True


def _load_clearml_task() -> Any:
    try:
        from clearml import Task  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS as exc:
        raise RuntimeError("ClearML is not available. Install clearml or disable run.clearml.enabled.") from exc
    return Task


def _coerce_task(task: Any) -> Any:
    return task if task is not None else NoOpTask()


def _get_logger(task: Any) -> Any:
    task = _coerce_task(task)
    getter = getattr(task, "get_logger", None)
    if callable(getter):
        return getter()
    return _NOOP_LOGGER
