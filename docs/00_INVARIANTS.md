# 不変条件（共通契約）

## 0. 目的（常に最優先）
- ClearML上で **非専門ユーザーが迷わず**「実行→比較→モデル選択→推論」できる。
- 開発者が ClearML/Hydra の深い知識なしでも拡張できる（拡張点＝registry + workflow hook）。

## 1. タスク独立性（Pipelineが“つなぐだけ”）
- `dataset_register`, `preprocess`, `train_model`, `train_parent`, `infer_*` は **単体で実行可能**。
- Pipeline実行時も **タスク内容は同一**（Pipeline専用の処理分岐を作らない）。

## 2. 比較可能性（再現性とフェア比較）
- split方式/seed/CV/metric は契約化し、勝手に変えない。
- 比較の単位は「同一dataset_id（もしくは同一 lineage）」×「同一評価ルール」。

## 3. データリーク禁止（skew禁止）
- 前処理は train/valid/test を跨いでfitしない。
- 推論は学習時と同じ前処理bundleを利用する（feature pipeline一致）。

## 4. ClearML UI Hygiene（誤認防止）
- HyperParameters: そのタスクの設定のみ（関連しない項目を出さない）。
- それ以外の関連情報は **User Properties** と **Artifacts** に配置。
- 親タスクは “意思決定” に必要な最小プロットのみ（リーダーボード中心）。

## 5. 省コード・レビュー容易性
- 「最小構成で最大拡張性」。不要な抽象化・重複ディレクトリ禁止。
- 重要箇所は `docs/15_CODEMAP.md` と docstring で「どこを見るべきか」を明示。
