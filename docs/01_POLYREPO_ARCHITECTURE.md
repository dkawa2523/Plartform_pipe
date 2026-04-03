# ポリレポ構成（Platform + Solutions）

## 目的
- 多用途開発の可読性・保守性を上げつつ、ClearML上で用途が混ざらない状態を作る
- 非DSユーザーが ClearML で「用途→Pipeline→結果」を迷わず追える

## リポジトリ分割

```mermaid
flowchart LR
  subgraph PlatformRepo[ml-platform]
    P1[ml_platform (python package)]
    P2[docs contracts]
    P3[codex_loop + agentskills]
  end
  subgraph SolutionRepo[ml-solution-<usecase>]
    S1[usecase package]
    S2[conf (Hydra)]
    S3[pipelines + registry extensions]
  end
  SolutionRepo -->|pip dependency pin| PlatformRepo
```

### Platform repo (ml-platform)
- **契約の正**: ClearML UI 契約、Artifacts契約、評価プロトコル
- **共通ライブラリ**: ClearML integration wrapper / core utilities / base workflows
- **テンプレ/スキル**: Codex運用ルール（AGENTS.md）、agentskills、codex_loop

### Solution repo (ml-solution-<usecase>)
- **用途固有**: conf、registry拡張、pipeline定義、README（非DS向け導線）
- ClearML上での識別: `project_name` と `usecase_id` を固定
- 実行: ローカル / ClearML Agent / ClearML UI clone の3パターンをサポート

## 重要: “混在” を防ぐルール
- SolutionにPlatformロジックをコピペしない（依存で解決）
- ClearML Project を用途別階層に固定（例: `MFG/<usecase>/...`）
- User Properties に `usecase_id` を必ず記録
