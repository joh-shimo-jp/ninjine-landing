# NINJINE Landing — スクリプト

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
| 出力 | `roadmap/index.html` |

### 公開 URL

- LP: https://joh-shimo-jp.github.io/ninjine-landing/
- ロードマップ: https://joh-shimo-jp.github.io/ninjine-landing/roadmap/

`public: false` および frontmatter なしのチケットは出力しません（AC-3）。

### テスト

```bash
python -m unittest scripts.test_generate_roadmap
```
