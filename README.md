# ninjine-landing

NINJINE の公開サイト（GitHub Pages）。会社ハブとして、ESHINE（外部リンク）・ご飯だよ！（内部 LP）への導線を提供する。

## サイト構成

| ページ | ファイル | 内容 | URL |
|---|---|---|---|
| 会社 INDEX | `index.html` | NINJINE ブランド表記の会社ハブ。ESHINE（外部リンク）・ご飯だよ！（内部リンク）への導線 | https://joh-shimo-jp.github.io/ninjine-landing/ |
| ご飯だよ！LP | `meal/index.html` | 「ご飯だよ！」紹介 LP（App Store Connect の Marketing URL / Support URL 用） | https://joh-shimo-jp.github.io/ninjine-landing/meal/ |
| 公式レシピ | `meal/recipes/` | GitHub Pages 公式レシピ。共有シートでアプリへテキスト取り込み | https://joh-shimo-jp.github.io/ninjine-landing/meal/recipes/ |

### ディレクトリ名 `meal/` と表示名「ご飯だよ！」の対応関係

- `meal/` はアプリ「ご飯だよ！」の紹介 LP を配置するディレクトリ名
- ディレクトリ名をリポジトリ名 `company/dev/apps/meal`（アプリ本体）・チケット呼称（`M-MON-01` 等）と統一することで、対外 URL と内部呼称の対応関係を辿るコストをなくしている
- 表示名（ユーザー・App Store 向け名称）は「ご飯だよ！」で変更なし。`meal` はあくまで内部・URL 上の識別子

### ESHINE への導線

`index.html` から ESHINE への外部リンクは以下を指す（`eshine-landing` リポジトリの公開 URL）。専用ページはこのリポジトリ内には作らない。

```
https://joh-shimo-jp.github.io/eshine-landing/
```

## デプロイ手順

- ブランチ: `main`
- 公開元: リポジトリルート（GitHub Pages）
- `index.html` 直下に配置されたファイル・ディレクトリがそのまま公開される（`meal/` 配下も含む）
- 変更を `main` にマージ・push すると GitHub Pages に自動反映される

## `roadmap/`（アーカイブ・現在未使用）

`roadmap/` ディレクトリはサイトから削除済み（N-LP-01・2026-07-25 改定）。理由: 会社ハブとしての再構成にあたり、STOP 中チケットが並ぶロードマップを主要導線に残すと停滞印象を与えるリスクがあるため。

ただし `scripts/generate_roadmap.py` 等の生成スクリプトは、`company/dev/queue/` の `public: true` チケットからロードマップ HTML を生成する資産として **リポジトリ内にアーカイブ（現在未使用）として保持** している（削除はしていない）。将来ロードマップ公開を再検討する際に再利用可能。通常のデプロイ・運用フローには含まれない。

```bash
# アーカイブ済みスクリプト（現在サイトのビルド・デプロイ対象外）
python scripts/generate_roadmap.py
```

詳細: [`scripts/README.md`](scripts/README.md)
