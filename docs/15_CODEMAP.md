# CODEMAP（重要箇所）

## Entry points（Library contract）
- `ml_platform` は実行CLIを持たないライブラリ専用構成
- 実行エントリポイントは usecase 側（例: `ml_taularanalysis/src/tabular_analysis/cli.py`）が保持
- `ml_platform` は config / workflow / integrations / core tabular の契約を提供

## Workflows
- Platform: `src/ml_platform/workflow/__init__.py`（契約を守る接着層）
- 実行アプリ側ワークフローは platform 契約に依存して拡張する

## Integrations
- `src/ml_platform/integrations/clearml/*`

## Core libraries
- Tabular primitives (schema/IO/bundle): `src/ml_platform/core/tabular/*`
- Registry contracts (models/metrics/preprocessors): `src/ml_platform/registry.py`

## Config helpers
- `src/ml_platform/config.py` (Hydra contract helpers, config export)
- `conf_templates/*` (task-root config templates)

## Tools
- Cleanup: `tools/cleanup_repo.py`（使い方: `docs/06_CODE_SIZE_AND_REVIEW.md`）
- Repo doctor: `tools/doctor.py`
- Codex loop guard: `tools/codex_loop/run.py`
