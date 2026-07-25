# NINJINE Landing — スクリプト

> **アーカイブ（現在未使用）**: `roadmap/` は N-LP-01（2026-07-25 改定）でサイトから削除され、`generate_roadmap.py` は通常のデプロイ・運用フローの対象外になっています。実行ロジック自体は変更していません（将来ロードマップ公開を再検討する際の再利用資産として保持）。

## generate_roadmap.py

`company/dev/queue/` の `public: true` チケットからロードマップ HTML を生成します。

### 実行

```bash
cd company/dev/apps/ninjine-landing
python scripts/generate_roadmap.py
```

### 入出力

| 項目 | パス |
|---|---|
| 入力 | `company/dev/queue/active/*.md`, `queue/done/*.md` |
| 出力 | `roadmap/index.html`（※ `roadmap/` はサイトから削除済み。再生成しても GitHub Pages には公開されない） |

### 公開 URL（現状）

- LP: https://joh-shimo-jp.github.io/ninjine-landing/
- ご飯だよ！: https://joh-shimo-jp.github.io/ninjine-landing/meal/
- ロードマップ: 非公開（アーカイブ）

`public: false` および frontmatter なしのチケットは出力しません（AC-3）。

### テスト

```bash
python -m unittest scripts.test_generate_roadmap
```
