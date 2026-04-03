# コード量抑制・レビュー容易性（共通）

- 最優先: 目的仕様（ClearMLで迷わない、拡張が安全）
- 次点: **できるだけコンパクト**（ファイルを増やさない、抽象化しすぎない）
- 重要入口は `docs/15_CODEMAP.md` に集約
- PR/変更は「影響範囲が追える」ことが最重要

## Cleanup
- 生成物は `tools/cleanup_repo.py` で掃除（.git/.venv は対象外）
- 対象例: outputs/multirun, dist/build, *.egg-info, cache類（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache）, .coverage/htmlcov, .clearml_cache, work/runs, work/_runner_state.json, .codex_exec_selfcheck.txt, .DS_Store
- 新しい生成物が増えたら `.gitignore` と `tools/cleanup_repo.py` を同時に更新
- dry-run: `python tools/cleanup_repo.py --repo . --dry-run`（`--apply` が無い場合の既定）
- delete: `python tools/cleanup_repo.py --repo . --apply`
- 任意の場所から実行する場合は `--repo <path>` を指定
