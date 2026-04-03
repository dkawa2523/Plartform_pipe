# ClearML Task UI 契約（共通）

この文書は **ClearML上でユーザーが迷わない**ためのUI設計契約です。  
各タスクは、**Configuration / HyperParameters / Info / Artifacts / Plots / Debug Samples** を以下の方針で埋めます。

## 共通原則
- HyperParameters: **そのタスクでユーザーが操作すべき値だけ**
- Full config: Artifact `config_full.yaml` に保存（再現性）
- User Properties: `usecase_id`, `dataset_id`, `model_id`, `score` 等の検索キー
- Plots: 最小化。親=比較、子=詳細。タイトルprefixで順序固定。
- Debug samples: 少量固定（テーブルならCSV少量）

---

## 実行モード（必須対応）
- Local mode: `run.clearml.enabled=false` で実行（ClearMLなし）
- ClearML logging mode: `run.clearml.enabled=true` でTask作成・ログ
- Agent mode: `enqueue=true` のとき `task.execute_remotely(queue_name=...)`（タスク単体）
- UI clone mode: `task.set_script(...)` を config で設定できる（repository/branch/entry_point）

---

## タスク別（最低限）
### preprocess（Dataset Task）
- Artifacts: `preprocess_recipe.json`, `preprocess_summary.md`, `bundle.joblib`, `schema_after.json`

### train_parent（Parent Task）
- Artifacts: `leaderboard.csv`, `run_manifest.json`
- Plots: `01_leaderboard_table`, `02_topk_bar` まで（最小）

### train_model（Child Task）
- Artifacts: `model.pkl`, `metrics.json`, `preds_valid.parquet`
- Plots: `01_pred_vs_true`, `02_residuals`, `03_feature_importance`（SHAPはoptional）

### inference（single/batch/optimize）
- Artifacts: モード別に `preds.csv`, `best_solution.json`, `trials.csv`

---

> 詳細は Platform repo の docs を正とし、Solution repo はそのスナップショットを保持する。
