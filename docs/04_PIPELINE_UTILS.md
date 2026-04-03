# Pipeline Utils (Platform)

## 目的
- Pipeline は司令塔のみ。step は単体実行と同一のタスク。
- parameter handoff をパターン化して重複を減らす。
- step_task_ids.json を残して DAG 追跡を楽にする。

## Minimal controller
```python
from ml_platform.integrations.clearml import pipeline_utils

controller = pipeline_utils.maybe_create_controller(cfg, name="usecase-pipeline")
if controller:
    pipeline_utils.require_clearml_agent("default")  # optional when using queue/agent
    controller.add_parameter("dataset_id", "ds_001")
    controller.add_parameter("model_id", "baseline")
```

## Parameter handoff patterns
```python
overrides = pipeline_utils.merge_param_overrides(
    pipeline_utils.handoff_dataset_id(),
    pipeline_utils.handoff_model_id(),
    pipeline_utils.handoff_step_task_id("preprocess", "task.preprocess_task_id"),
)
```

## step_task_ids.json
```python
step_task_ids = {
    "preprocess": preprocess_task,
    "train_parent": train_parent_task,
}
pipeline_utils.write_step_task_ids(step_task_ids, cfg=cfg)
```

## reuse_last_task_id 固定
```python
reuse_last_task_id = pipeline_utils.fixed_reuse_last_task_id()
```
