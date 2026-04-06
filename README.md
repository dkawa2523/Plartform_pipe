# ml-platform

`ml-platform` は、solution repository から再利用するための **共通 ML platform library** です。

主な責務:

- Hydra の root config / 共通 group 契約
- ClearML integration helper
- artifact / manifest / hashing / versioning
- tabular 向け core primitives
- pipeline utility と task UI hygiene

この repo は **standalone の業務 pipeline application ではありません**。  
end-to-end の学習 pipeline や infer pipeline は、これを依存に持つ solution repo 側で実行します。

## まず最初に読む

- [SETUP.md](SETUP.md)
- [docs/README.md](docs/README.md)

## この repo で確認できること

- platform package が新しい PC で install できる
- pytest ベースの contract / utility test が通る
- 必要なら ClearML への最小 smoke を行える
- downstream solution repo がこの platform repo を dependency として参照できる

## よくある利用シーン

1. `ml_platform` を新しい Git repository に移す
2. 新しい PC で platform を install する
3. contract と utility の smoke を回す
4. downstream solution repo の dependency をこの repo に向ける
5. solution repo 側で template sync と pipeline rehearsal を行う

## 注意

- この repo 単体では、solution 固有の seed pipeline や infer task は作成しません
- ClearML 上の visible pipeline / operator flow は solution repo 側の責務です
- platform 側では、ClearML task contract と reusable helper の正しさを担保します
