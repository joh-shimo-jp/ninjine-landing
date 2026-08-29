#!/usr/bin/env python3
"""M-DIST-02: Build catalog.json and recipe HTML pages from template + extras."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extra_recipes_data import RECIPES as EXTRA_RECIPES

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
TEMPLATE_PACK = (
    Path(__file__).resolve().parents[4]
    / "meal/assets/data/template_gift_pack.json"
)

CATEGORY_LABEL = {"main": "主菜", "side": "副菜", "soup": "汁物"}

TEMPLATE_SLUGS = {
    "template-initial-main": "tori-teriyaki",
    "template-initial-side": "horenso-gomaae",
    "template-initial-soup": "tofu-wakame-misoshiru",
    "template-pool-01": "buta-shogayaki",
    "template-pool-02": "oyakodon",
    "template-pool-03": "kinpira-gobo",
    "template-pool-04": "kabocha-nimono",
    "template-pool-05": "tonjiru",
    "template-pool-06": "nameko-misoshiru",
    "template-pool-07": "mabo-dofu",
    "template-pool-08": "komatsuna-ohitashi",
}


def search_keywords(recipe: dict) -> str:
    parts = [recipe["name"], CATEGORY_LABEL[recipe["category"]]]
    parts.extend(recipe.get("tags") or [])
    for ing in recipe.get("ingredients") or []:
        parts.append(ing["name"])
    return " ".join(parts)


DEFAULT_STEP_MINUTES = {"準備": 5, "加熱": 10, "仕上げ": 3}


def step_minutes(step: dict) -> int | None:
    if step.get("timerMinutes") is not None:
        return int(step["timerMinutes"])
    sec = step.get("timerSeconds")
    if sec:
        return max(1, round(int(sec) / 60))
    return None


def enrich_step_times(steps: list[dict]) -> list[dict]:
    out: list[dict] = []
    for raw in steps:
        step = dict(raw)
        mins = step_minutes(step)
        if mins is None:
            text = step.get("text", "")
            match = re.search(r"(\d+)\s*分", text)
            if match:
                snippet = text[match.start() : match.end() + 2]
                if "短" not in snippet and "早" not in snippet:
                    mins = int(match.group(1))
            if mins is None:
                mins = DEFAULT_STEP_MINUTES.get(step.get("label", ""))
        if mins is not None:
            step["timerMinutes"] = int(mins)
            # Keep timerSeconds for template fidelity when originally present.
            if "timerSeconds" not in step and step.get("timerMinutes"):
                step["timerSeconds"] = int(step["timerMinutes"]) * 60
        out.append(step)
    return out


def step_label_html(step: dict) -> str:
    label = html.escape(step["label"])
    mins = step_minutes(step)
    if mins is None:
        return f'<span class="step-label">{label}</span>'
    return (
        f'<span class="step-head">'
        f'<span class="step-label">{label}</span>'
        f'<span class="step-time">{mins}分</span>'
        f"</span>"
    )


def step_share_text(step: dict) -> str:
    # M-IMPORT-01: `- 分類 | 内容` only. Recipe-level 所要時間 is `調理時間:`.
    # Step minutes are web UI only (アプリの手順タイマーは現行フォーマット非対応).
    return f"- {step['label']} | {step['text']}"


def meal_share_text(recipe: dict) -> str:
    cat = CATEGORY_LABEL[recipe["category"]]
    tags = ", ".join(recipe.get("tags") or [])
    lines = [
        f"献立名: {recipe['name']}",
        f"分類: {cat}",
        f"人数: {recipe['servings']}",
        f"調理時間: {recipe['timeMinutes']}分",
        f"タグ: {tags}",
        "",
        "## 食材",
    ]
    for ing in recipe["ingredients"]:
        lines.append(f"- {ing['name']} | {ing['qty']}")
    lines.append("")
    lines.append("## 手順")
    for step in recipe["steps"]:
        lines.append(step_share_text(step))
    return "\n".join(lines) + "\n"


def normalize_template_entry(entry: dict, slug: str) -> dict:
    steps = []
    for s in entry["steps"]:
        step = {"label": s["label"], "text": s["text"]}
        if s.get("timerSeconds") is not None:
            step["timerSeconds"] = s["timerSeconds"]
        steps.append(step)
    return {
        "slug": slug,
        "id": entry["id"],
        "name": entry["name"],
        "category": entry["category"],
        "categoryLabel": CATEGORY_LABEL[entry["category"]],
        "timeMinutes": entry["timeMinutes"],
        "tags": entry["tags"],
        "servings": entry["servings"],
        "ingredients": entry["ingredients"],
        "steps": enrich_step_times(steps),
    }


def build_catalog() -> list[dict]:
    pack = json.loads(TEMPLATE_PACK.read_text(encoding="utf-8"))
    recipes: list[dict] = []
    for entry in pack["initialSet"] + pack["dailyPool"]:
        slug = TEMPLATE_SLUGS[entry["id"]]
        r = normalize_template_entry(entry, slug)
        r["searchKeywords"] = search_keywords(r)
        recipes.append(r)

    for entry in EXTRA_RECIPES:
        recipe = dict(entry)
        recipe["categoryLabel"] = CATEGORY_LABEL[recipe["category"]]
        recipe["steps"] = enrich_step_times(list(recipe["steps"]))
        recipe["searchKeywords"] = search_keywords(recipe)
        recipes.append(recipe)

    if len(recipes) != 50:
        raise SystemExit(f"Expected 50 recipes, got {len(recipes)}")
    return recipes


def render_detail(recipe: dict) -> str:
    name = html.escape(recipe["name"])
    cat = html.escape(recipe["categoryLabel"])
    tags = html.escape(" / ".join(recipe.get("tags") or []))
    share = html.escape(meal_share_text(recipe))

    ing_lines = "\n".join(
        f'        <li>{html.escape(i["name"])} <span class="ing-qty">{html.escape(i["qty"])}</span></li>'
        for i in recipe["ingredients"]
    )
    step_lines = "\n".join(
        f"""        <li>
          {step_label_html(s)}
          <p>{html.escape(s["text"])}</p>
        </li>"""
        for s in recipe["steps"]
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — ご飯だよ！公式レシピ</title>
  <meta name="description" content="ご飯だよ！公式レシピ：{name}。共有シートからアプリへ取り込めます。">
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/favicon-32.png">
  <link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Noto Serif JP', 'Hiragino Mincho ProN', 'Yu Mincho', serif;
      background: #FAFAF8; color: #2A2A2A; line-height: 1.75; min-height: 100vh;
    }}
    main {{ max-width: 640px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
    .eyebrow {{ font-size: 0.72rem; letter-spacing: 0.12em; color: #8B7355; text-transform: uppercase; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 1.7rem; letter-spacing: 0.06em; margin-bottom: 0.35rem; font-weight: 700; }}
    .meta {{ color: #6A6A6A; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    .meta span + span::before {{ content: " · "; color: #C4B8A8; }}
    .section {{ margin: 1.5rem 0; padding: 1.25rem 1.35rem 1.4rem; background: #fff; border: 1px solid #DDDBD5; border-radius: 8px; }}
    .section h2 {{ font-size: 1.05rem; letter-spacing: 0.04em; margin-bottom: 0.75rem; font-weight: 600; }}
    ul {{ list-style: none; }}
    ul li {{ margin: 0.4rem 0; color: #4A4A4A; font-size: 0.95rem; padding-left: 0.9rem; position: relative; }}
    ul li::before {{ content: "—"; position: absolute; left: 0; color: #8B7355; }}
    .ing-qty {{ color: #6A6A6A; }}
    .steps li {{ margin: 0.85rem 0; }}
    .step-head {{ display: inline-flex; align-items: center; gap: 0.35rem; margin-bottom: 0.25rem; }}
    .step-label {{ display: inline-block; font-size: 0.75rem; color: #8B7355; border: 1px solid #C4B8A8; border-radius: 4px; padding: 0.05rem 0.45rem; letter-spacing: 0.06em; }}
    .step-time {{ font-size: 0.82rem; color: #4A3728; font-weight: 600; letter-spacing: 0.04em; }}
    .howto {{ font-size: 0.88rem; color: #4A4A4A; }}
    .howto ol {{ margin: 0.6rem 0 0 1.2rem; }}
    .howto li {{ margin: 0.35rem 0; }}
    .cta {{ margin-top: 1.5rem; display: flex; flex-direction: column; gap: 0.65rem; align-items: stretch; }}
    .btn {{ display: inline-block; text-align: center; padding: 0.7rem 1.25rem; border-radius: 6px; text-decoration: none; font-size: 0.92rem; border: 1px solid #2A2A2A; color: #2A2A2A; background: transparent; cursor: pointer; font-family: inherit; transition: background 0.15s; }}
    .btn:hover {{ background: #F0EDE5; }}
    .btn-primary {{ background: #2A2A2A; color: #FAFAF8; border-color: #2A2A2A; }}
    .btn-primary:hover {{ background: #4A3728; border-color: #4A3728; }}
    .status {{ min-height: 1.25rem; margin-top: 0.5rem; font-size: 0.82rem; color: #6A6A6A; text-align: center; }}
    .status.is-ok {{ color: #3D6B4F; }}
    .status.is-err {{ color: #8B3A3A; }}
    pre.share-text {{ display: none; }}
    footer {{ margin-top: 2.5rem; font-size: 0.78rem; color: #6A6A6A; text-align: center; }}
    footer a {{ color: #4A3728; text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Official recipe</p>
    <h1>{name}</h1>
    <p class="meta">
      <span>{cat}</span>
      <span>{recipe["servings"]}人分</span>
      <span>約{recipe["timeMinutes"]}分</span>
      <span>{tags}</span>
    </p>
    <section class="section" aria-labelledby="ing-title">
      <h2 id="ing-title">食材</h2>
      <ul>
{ing_lines}
      </ul>
    </section>
    <section class="section" aria-labelledby="steps-title">
      <h2 id="steps-title">手順</h2>
      <ul class="steps">
{step_lines}
      </ul>
    </section>
    <section class="section" aria-labelledby="send-title">
      <h2 id="send-title">ご飯だよ！に送る</h2>
      <div class="howto">
        <p>下のボタンでレシピテキストを共有し、共有先で「ご飯だよ！」を選んでください。アプリがレシピを取り込み、<strong>自動で保存</strong>します。</p>
        <ol>
          <li>「ご飯だよ！に送る」をタップ</li>
          <li>共有シートで「ご飯だよ！」を選ぶ</li>
          <li>アプリでレシピが追加されたことを確認</li>
        </ol>
      </div>
      <div class="cta">
        <button type="button" class="btn btn-primary" id="share-to-meal">ご飯だよ！に送る</button>
        <button type="button" class="btn" id="copy-meal-text">テキストをコピー</button>
      </div>
      <p class="status" id="share-status" role="status" aria-live="polite"></p>
    </section>
    <pre class="share-text" id="meal-share-text" hidden>{share}</pre>
    <footer>
      <p><a href="../">← 公式レシピ一覧</a> · <a href="../../">ご飯だよ！LP</a></p>
      <p>© 2026 NINJINE — ご飯だよ！</p>
    </footer>
  </main>
  <script>
    (function () {{
      var source = document.getElementById('meal-share-text');
      var statusEl = document.getElementById('share-status');
      var text = (source.textContent || '').replace(/^\\n+/, '').replace(/\\n+$/, '') + '\\n';
      function setStatus(msg, ok) {{
        statusEl.textContent = msg || '';
        statusEl.classList.remove('is-ok', 'is-err');
        if (msg) statusEl.classList.add(ok ? 'is-ok' : 'is-err');
      }}
      function copyText() {{
        if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
        var ta = document.createElement('textarea');
        ta.value = text; ta.setAttribute('readonly', '');
        ta.style.position = 'fixed'; ta.style.left = '-9999px';
        document.body.appendChild(ta); ta.select();
        try {{ document.execCommand('copy'); return Promise.resolve(); }}
        catch (e) {{ return Promise.reject(e); }}
        finally {{ document.body.removeChild(ta); }}
      }}
      document.getElementById('copy-meal-text').addEventListener('click', function () {{
        copyText().then(function () {{ setStatus('コピーしました。', true); }}).catch(function () {{ setStatus('コピーに失敗しました。', false); }});
      }});
      document.getElementById('share-to-meal').addEventListener('click', function () {{
        if (navigator.share) {{
          navigator.share({{ text: text }}).then(function () {{ setStatus('共有シートを開きました。', true); }}).catch(function (err) {{
            if (err && err.name === 'AbortError') {{ setStatus('', true); return; }}
            copyText().then(function () {{ setStatus('共有できないためコピーしました。', true); }});
          }});
          return;
        }}
        copyText().then(function () {{ setStatus('このブラウザは共有非対応のためコピーしました。', true); }});
      }});
    }})();
  </script>
</body>
</html>
"""


def render_index() -> str:
    return """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>公式レシピ — ご飯だよ！</title>
  <meta name="description" content="ご飯だよ！公式レシピ一覧。キーワード検索・共有シートからアプリへ取り込めます。">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png">
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Noto Serif JP', 'Hiragino Mincho ProN', 'Yu Mincho', serif; background: #FAFAF8; color: #2A2A2A; line-height: 1.75; min-height: 100vh; }
    main { max-width: 640px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
    .eyebrow { font-size: 0.72rem; letter-spacing: 0.12em; color: #8B7355; text-transform: uppercase; margin-bottom: 0.5rem; }
    h1 { font-size: 1.6rem; letter-spacing: 0.08em; margin-bottom: 0.5rem; }
    .lead { color: #6A6A6A; font-size: 0.95rem; margin-bottom: 1.25rem; }
    .search-wrap { margin-bottom: 1.25rem; }
    .search-wrap label { display: block; font-size: 0.82rem; color: #6A6A6A; margin-bottom: 0.35rem; }
    .search-wrap input {
      width: 100%; padding: 0.75rem 1rem; font-size: 1rem; font-family: inherit;
      border: 1px solid #DDDBD5; border-radius: 8px; background: #fff;
    }
    .search-wrap input:focus { outline: 2px solid #8B7355; outline-offset: 1px; }
    .count { font-size: 0.82rem; color: #9A9A9A; margin-bottom: 0.75rem; }
    .list { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
    .list a {
      display: block; padding: 1.1rem 1.25rem; background: #fff;
      border: 1px solid #DDDBD5; border-radius: 8px; text-decoration: none;
      color: #2A2A2A; transition: background 0.15s;
    }
    .list a:hover { background: #F7F4EE; }
    .list .name { font-size: 1.05rem; font-weight: 600; letter-spacing: 0.04em; }
    .list .meta { margin-top: 0.25rem; font-size: 0.82rem; color: #6A6A6A; }
    .empty { padding: 2rem 1rem; text-align: center; color: #9A9A9A; font-size: 0.92rem; }
    .note { margin-top: 1.5rem; font-size: 0.8rem; color: #9A9A9A; }
    footer { margin-top: 2.5rem; font-size: 0.78rem; color: #6A6A6A; text-align: center; }
    footer a { color: #4A3728; text-decoration: none; }
    footer a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Official recipes</p>
    <h1>公式レシピ</h1>
    <p class="lead">各レシピページから、共有シート経由で「ご飯だよ！」へ取り込めます。</p>
    <div class="search-wrap">
      <label for="recipe-search">レシピを検索</label>
      <input type="search" id="recipe-search" placeholder="料理名・食材・タグ（例: 鶏、パスタ、味噌）" autocomplete="off">
    </div>
    <p class="count" id="result-count" aria-live="polite"></p>
    <ul class="list" id="recipe-list"></ul>
    <p class="empty" id="empty-msg" hidden>該当するレシピがありません。</p>
    <p class="note">※ 「ご飯だよ！に送る」からアプリへ取り込めます。レシピは随時追加します。</p>
    <footer>
      <p><a href="../">← ご飯だよ！LP</a></p>
      <p>© 2026 NINJINE — ご飯だよ！</p>
    </footer>
  </main>
  <script>
    (function () {
      var listEl = document.getElementById('recipe-list');
      var countEl = document.getElementById('result-count');
      var emptyEl = document.getElementById('empty-msg');
      var input = document.getElementById('recipe-search');
      var all = [];

      function categoryLabel(c) {
        return { main: '主菜', side: '副菜', soup: '汁物' }[c] || c;
      }

      function render(items) {
        listEl.innerHTML = '';
        items.forEach(function (r) {
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = r.slug + '/';
          var tags = (r.tags || []).join(' / ');
          a.innerHTML = '<p class="name">' + r.name + '</p><p class="meta">' +
            categoryLabel(r.category) + ' · 約' + r.timeMinutes + '分 · ' + r.servings + '人分' +
            (tags ? ' · ' + tags : '') + '</p>';
          li.appendChild(a);
          listEl.appendChild(li);
        });
        countEl.textContent = items.length + '件 / 全' + all.length + '件';
        emptyEl.hidden = items.length > 0;
      }

      function filter(q) {
        var needle = (q || '').trim().toLowerCase();
        if (!needle) return render(all);
        var tokens = needle.split(/\\s+/).filter(Boolean);
        render(all.filter(function (r) {
          var hay = (r.searchKeywords || r.name).toLowerCase();
          return tokens.every(function (t) { return hay.indexOf(t) !== -1; });
        }));
      }

      fetch('catalog.json')
        .then(function (res) { return res.json(); })
        .then(function (data) {
          all = data.recipes || [];
          all.sort(function (a, b) { return a.name.localeCompare(b.name, 'ja'); });
          render(all);
        })
        .catch(function () {
          countEl.textContent = '一覧の読み込みに失敗しました。';
        });

      input.addEventListener('input', function () { filter(input.value); });
    })();
  </script>
</body>
</html>
"""


def main() -> None:
    recipes = build_catalog()
    western_pasta = sum(
        1
        for r in recipes
        if any(t in ("洋食", "パスタ") for t in (r.get("tags") or []))
    )
    if western_pasta < 10:
        raise SystemExit(f"Need 10+ western/pasta recipes, got {western_pasta}")

    catalog = {
        "version": 1,
        "updated": "2026-08-29",
        "count": len(recipes),
        "recipes": recipes,
    }
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for recipe in recipes:
        slug_dir = ROOT / recipe["slug"]
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "index.html").write_text(render_detail(recipe), encoding="utf-8")

    (ROOT / "index.html").write_text(render_index(), encoding="utf-8")
    print(f"Generated {len(recipes)} recipes ({western_pasta} western/pasta)")


if __name__ == "__main__":
    main()
