# Hydra Config Contract (Platform)

## Task roots
- Root config names: `preprocess`, `train`, `infer`, `pipeline`
- Each root composes common groups: `run`, `seed`, `data`, `eval`
- Task-specific settings live under `task/<task>/...`

## Full config export
- Do not connect the full config to ClearML HyperParameters
- Always export the full config as Artifact `config_full.yaml`
- Use `ml_platform.config.export_config_artifact(cfg, task=task)`

## Override examples
```bash
python -m usecase.cli.train --config-name train \
  data.dataset_id=ds_001 task.model_id=baseline run.clearml.enabled=true

python -m usecase.cli.preprocess --config-name preprocess \
  seed.global=123 +eval.metric=mae
```

## Templates
- Copy `conf_templates/` into the solution repo `conf/` as a starting point
