"""Platform workflow base implementations (hook-driven)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from ml_platform.common.config_utils import cfg_value as _cfg_value
from ml_platform.config import resolve_output_dir
from ml_platform.integrations.clearml import (
    apply_ui_hygiene,
    report_plotly,
    report_scalar,
    report_table,
    task_factory,
    upload_artifact,
)

__all__ = [
    "WORKFLOW_REGISTRY",
    "WorkflowContext",
    "WorkflowLogger",
    "WorkflowRegistry",
    "dataset_register",
    "infer",
    "preprocess",
    "train_model",
    "train_parent",
]

HookFn = Callable[..., Any]
_OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError)


@dataclass(frozen=True)
class WorkflowContext:
    cfg: Any
    task: Any
    output_dir: Path


@dataclass
class WorkflowRegistry:
    dataset_register: HookFn | None = None
    preprocess: HookFn | None = None
    train_model: HookFn | None = None
    train_parent: HookFn | None = None
    infer: HookFn | None = None

    def resolve(self, name: str, hook: HookFn | None) -> HookFn:
        if hook is not None:
            return hook
        selected = getattr(self, name, None)
        if selected is None:
            raise NotImplementedError(f"Workflow hook not registered: {name}")
        return selected


WORKFLOW_REGISTRY = WorkflowRegistry()


@dataclass
class WorkflowLogger:
    task: Any
    cfg: Any
    output_dir: Path
    hparams: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def set_hparams(self, hparams: Mapping[str, Any] | None) -> None:
        if not hparams:
            return
        self.hparams.update(dict(hparams))

    def set_properties(self, properties: Mapping[str, Any] | None) -> None:
        if not properties:
            return
        self.properties.update(dict(properties))

    def upload_artifact(self, name: str, artifact: Any) -> None:
        upload_artifact(self.task, name, artifact)

    def log_preprocess_artifacts(
        self,
        *,
        recipe: Any | None = None,
        summary: Any | None = None,
        bundle: Any | None = None,
        schema_after: Any | None = None,
    ) -> None:
        self._maybe_upload("preprocess_recipe.json", recipe)
        self._maybe_upload("preprocess_summary.md", summary)
        self._maybe_upload("bundle.joblib", bundle)
        self._maybe_upload("schema_after.json", schema_after)

    def log_train_parent_artifacts(
        self,
        *,
        leaderboard: Any | None = None,
        run_manifest: Any | None = None,
    ) -> None:
        self._maybe_upload("leaderboard.csv", leaderboard)
        self._maybe_upload("run_manifest.json", run_manifest)

    def log_train_model_artifacts(
        self,
        *,
        model: Any | None = None,
        metrics: Any | None = None,
        preds_valid: Any | None = None,
    ) -> None:
        self._maybe_upload("model.pkl", model)
        self._maybe_upload("metrics.json", metrics)
        self._maybe_upload("preds_valid.parquet", preds_valid)

    def log_infer_artifacts(
        self,
        *,
        preds: Any | None = None,
        best_solution: Any | None = None,
        trials: Any | None = None,
    ) -> None:
        self._maybe_upload("preds.csv", preds)
        self._maybe_upload("best_solution.json", best_solution)
        self._maybe_upload("trials.csv", trials)

    def log_leaderboard_table(
        self,
        *,
        table: Any | None = None,
        csv: str | None = None,
        series: str = "leaderboard",
        iteration: int = 0,
    ) -> None:
        if table is None and csv is None:
            return
        report_table(self.task, "01_leaderboard_table", series, table=table, csv=csv, iteration=iteration)

    def log_topk_bar(
        self,
        plot: Any | None,
        *,
        series: str = "topk",
        iteration: int = 0,
    ) -> None:
        if plot is None:
            return
        report_plotly(self.task, "02_topk_bar", series, plot, iteration=iteration)

    def log_pred_vs_true(
        self,
        plot: Any | None,
        *,
        series: str = "pred_vs_true",
        iteration: int = 0,
    ) -> None:
        if plot is None:
            return
        report_plotly(self.task, "01_pred_vs_true", series, plot, iteration=iteration)

    def log_residuals(
        self,
        plot: Any | None,
        *,
        series: str = "residuals",
        iteration: int = 0,
    ) -> None:
        if plot is None:
            return
        report_plotly(self.task, "02_residuals", series, plot, iteration=iteration)

    def log_feature_importance(
        self,
        plot: Any | None,
        *,
        series: str = "feature_importance",
        iteration: int = 0,
    ) -> None:
        if plot is None:
            return
        report_plotly(self.task, "03_feature_importance", series, plot, iteration=iteration)

    def report_scalar(
        self,
        title: str,
        series: str,
        value: float,
        *,
        iteration: int = 0,
    ) -> None:
        report_scalar(self.task, title, series, value, iteration=iteration)

    def finalize(self) -> None:
        hparams = self.hparams or None
        properties = self.properties or None
        apply_ui_hygiene(self.task, self.cfg, hparams=hparams, properties=properties, output_dir=self.output_dir)

    def _maybe_upload(self, name: str, artifact: Any | None) -> None:
        if artifact is None:
            return
        self.upload_artifact(name, artifact)


def dataset_register(cfg: Any, *, hook: HookFn | None = None, registry: WorkflowRegistry = WORKFLOW_REGISTRY, **kwargs: Any) -> Any:
    return _run_workflow("dataset_register", cfg, hook=hook, registry=registry, **kwargs)


def preprocess(cfg: Any, *, hook: HookFn | None = None, registry: WorkflowRegistry = WORKFLOW_REGISTRY, **kwargs: Any) -> Any:
    return _run_workflow("preprocess", cfg, hook=hook, registry=registry, **kwargs)


def train_model(cfg: Any, *, hook: HookFn | None = None, registry: WorkflowRegistry = WORKFLOW_REGISTRY, **kwargs: Any) -> Any:
    return _run_workflow("train_model", cfg, hook=hook, registry=registry, **kwargs)


def train_parent(cfg: Any, *, hook: HookFn | None = None, registry: WorkflowRegistry = WORKFLOW_REGISTRY, **kwargs: Any) -> Any:
    return _run_workflow("train_parent", cfg, hook=hook, registry=registry, **kwargs)


def infer(cfg: Any, *, hook: HookFn | None = None, registry: WorkflowRegistry = WORKFLOW_REGISTRY, **kwargs: Any) -> Any:
    return _run_workflow("infer", cfg, hook=hook, registry=registry, **kwargs)


def _run_workflow(name: str, cfg: Any, *, hook: HookFn | None, registry: WorkflowRegistry, **kwargs: Any) -> Any:
    task = task_factory(cfg, task_type=_task_type(name))
    output_dir = resolve_output_dir(cfg, ".")
    logger = WorkflowLogger(task=task, cfg=cfg, output_dir=output_dir)
    logger.set_properties(_default_properties(cfg))
    context = WorkflowContext(cfg=cfg, task=task, output_dir=output_dir)
    handler = registry.resolve(name, hook)
    result = handler(context, logger, **kwargs)
    logger.finalize()
    return result


def _task_type(name: str) -> Any | None:
    try:
        from clearml import Task  # type: ignore
    except _OPTIONAL_IMPORT_ERRORS:
        return None
    mapping = {
        "dataset_register": Task.TaskTypes.data_processing,
        "preprocess": Task.TaskTypes.data_processing,
        "train_model": Task.TaskTypes.training,
        "train_parent": Task.TaskTypes.training,
        "infer": Task.TaskTypes.inference,
    }
    return mapping.get(name)


def _default_properties(cfg: Any) -> dict[str, Any]:
    usecase_id = (
        _cfg_value(cfg, "usecase_id")
        or _cfg_value(cfg, "data.usecase_id")
        or _cfg_value(cfg, "run.usecase_id")
    )
    return {"usecase_id": usecase_id or "unknown"}
