# Manifest / Hashing / Versioning Contract

This document defines the stable cross-solution contract for manifest.json, hashing,
versioning, and contract linting. Solution repos should follow it unchanged.

## Required artifacts (contract lint)
- output_dir must contain: config_resolved.yaml, out.json, manifest.json
- linted by ml_platform.contract.lint_contract and tools/doctor.py --output-dir
- do not rename or move these without updating the platform contract

## Required ClearML user properties
- platform_version
- code_version
- schema_version
- set automatically by ml_platform.integrations.clearml.task_factory (when run.clearml.enabled=true)
- keep keys stable for search and comparison

## Manifest schema (manifest.json)
Required top-level keys:
- schema_version
- code_version
- platform_version
- inputs
- outputs
- hashes

Required hashes:
- config_hash
- split_hash
- recipe_hash

Notes:
- inputs/outputs/hashes must be mappings (dataclasses and OmegaConf are coerced)
- use build_manifest() and write_manifest() from ml_platform.artifacts

Example:
```json
{
  "schema_version": "v1",
  "code_version": "git-sha",
  "platform_version": "0.1.0",
  "inputs": {"dataset_id": "foo", "split_id": "bar"},
  "outputs": {"model_id": "baz", "metric": 0.91},
  "hashes": {
    "config_hash": "...",
    "split_hash": "...",
    "recipe_hash": "..."
  },
  "extensions": {
    "usecase": {"note": "optional"}
  }
}
```

## Hash meaning
- config_hash: deterministic hash of resolved config used for the run
- split_hash: deterministic hash of data split definition (seed/folds/ids)
- recipe_hash: deterministic hash of preprocessing/training/inference recipe
- hashing uses normalized JSON with sorted keys and sha256, so same content -> same hash

## Version sources
- platform_version: package version (ml-platform/ml_platform) or pyproject.toml
- code_version: git rev-parse HEAD from repo root (or "unknown")
- schema_version: first match in config paths:
  - schema_version
  - schema.version
  - data.schema_version
  - data.schema.version
  - task.schema_version
  - task.schema.version

## Extension and namespace rules
- extra fields must be namespaced to avoid collisions
- prefer an extensions mapping with a stable namespace key (usecase, model, team, etc)
- additional hashes should live under hashes and be prefixed with a namespace
  (for example usecase_feature_hash)
- extra artifacts/properties must not replace required ones
- if a solution adds new required artifacts, extend linting by passing
  required_artifacts to lint_contract/assert_contract in that solution

## ClearML artifact note
- run_manifest.json is a UI artifact for train_parent (leaderboard runs)
- manifest.json is the canonical contract artifact for output_dir and linting
