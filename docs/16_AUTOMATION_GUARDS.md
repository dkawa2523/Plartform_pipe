# Codex ループ誤DONE防止（共通）

- Codex rc!=0 なら DONE不可
- 差分が出ないなら DONE不可
- task md 未更新なら DONE不可
- NONCE が task md に無いなら DONE不可
- Verification が通らないなら DONE不可

この仕組みは `tools/codex_loop/run.py` に実装されている。
