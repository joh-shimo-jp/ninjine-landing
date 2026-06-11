#!/usr/bin/env python3
"""
N-BIP-02: 公開ロードマップ生成スクリプト
入力: company/dev/queue/active/*.md および company/dev/queue/done/*.md
出力: roadmap/index.html

実行方法:
    python scripts/generate_roadmap.py

フィルタ: frontmatter の public: true のみ出力（public: false / frontmatter なしはスキップ）
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

# ===== パス設定 =====
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
OUTPUT_PATH = REPO_ROOT / "roadmap" / "index.html"

# company/dev/queue への絶対パス（scripts/ → ninjine-landing → apps → dev → queue）
QUEUE_BASE = SCRIPT_DIR.parent.parent.parent / "queue"
ACTIVE_DIR = QUEUE_BASE / "active"
DONE_DIR = QUEUE_BASE / "done"

# ===== ステータス設定 =====
STATUS_CONFIG = {
    "seed": {
        "label": "Seed",
        "color": "#8B7355",
        "bg": "#F5EDD8",
        "border": "#C4A882",
        "description": "アイデア・気づきの起点",
        "order": 1,
    },
    "goal": {
        "label": "Goal",
        "color": "#4A6B8A",
        "bg": "#E8F0F8",
        "border": "#7AADC8",
        "description": "受入条件・ゴール定義済み",
        "order": 2,
    },
    "task": {
        "label": "Task",
        "color": "#5A7A3A",
        "bg": "#EAF3E0",
        "border": "#8AB868",
        "description": "実装タスク分解・実装中",
        "order": 3,
    },
    "ship": {
        "label": "Ship",
        "color": "#7A3A6A",
        "bg": "#F3E0F0",
        "border": "#B868A8",
        "description": "成果物出力・検証中",
        "order": 4,
    },
    "delivered": {
        "label": "Delivered",
        "color": "#2A2A2A",
        "bg": "#EDEDED",
        "border": "#AAAAAA",
        "description": "完了・クローズ済み",
        "order": 5,
    },
}

# ===== frontmatter パース =====

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    YAML frontmatter を解析して (frontmatter_dict, body) を返す。
    frontmatter が存在しない場合は ({}, 全文) を返す。
    """
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = content[match.end():]
    fm = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # boolean
        if val.lower() == "true":
            fm[key] = True
        elif val.lower() == "false":
            fm[key] = False
        # リスト (例: ["tag1", "tag2"])
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            items = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
            fm[key] = items
        # 文字列（引用符を除去）
        else:
            fm[key] = val.strip('"').strip("'")
    return fm, body


def extract_title(body: str, ticket_id: str) -> str:
    """markdown body から最初の # 見出しを抽出。なければ ID を返す。"""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ticket_id


def extract_summary(body: str) -> str:
    """body から概要セクションを抽出（最初の非空段落 or 概要見出し直後）。"""
    lines = body.splitlines()
    in_summary = False
    summary_lines = []

    for line in lines:
        stripped = line.strip()
        # ## 概要 セクションを優先
        if re.match(r"^#{1,3}\s*(概要|Summary|description)", stripped, re.IGNORECASE):
            in_summary = True
            continue
        if in_summary:
            if stripped.startswith("#"):
                break
            if stripped:
                summary_lines.append(stripped)
                if len(summary_lines) >= 3:
                    break

    if summary_lines:
        return " ".join(summary_lines)

    # フォールバック: h1 の次の段落
    skip_h1 = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            skip_h1 = True
            continue
        if skip_h1 and stripped and not stripped.startswith("#") and not stripped.startswith("-") and not stripped.startswith("|"):
            return stripped[:200]

    return ""


# ===== チケット読み込み =====

def load_tickets(directory: Path) -> list[dict]:
    """
    ディレクトリ内の .md ファイルを読み込み、public: true のチケットのみ返す。
    スキップしたファイルはログに記録する。
    """
    tickets = []
    skipped_no_fm = []
    skipped_private = []

    if not directory.exists():
        print(f"[WARN] ディレクトリが存在しません: {directory}", file=sys.stderr)
        return tickets

    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)

        if not fm:
            skipped_no_fm.append(path.name)
            continue

        if fm.get("public") is not True:
            skipped_private.append(path.name)
            continue

        ticket_id = fm.get("id", path.stem)
        status = fm.get("status", "seed").lower()
        if status not in STATUS_CONFIG:
            status = "seed"

        tickets.append({
            "id": ticket_id,
            "status": status,
            "product": fm.get("product", ""),
            "tags": fm.get("tags", []),
            "created": fm.get("created", ""),
            "updated": fm.get("updated", ""),
            "title": extract_title(body, ticket_id),
            "summary": extract_summary(body),
        })

    print(f"[INFO] {directory.name}/ — 公開: {len(tickets)}, 非公開スキップ: {len(skipped_private)}, frontmatterなし: {len(skipped_no_fm)}", file=sys.stderr)
    if skipped_private:
        print(f"  [PRIVATE] {', '.join(skipped_private)}", file=sys.stderr)
    if skipped_no_fm:
        print(f"  [NO-FM]   {', '.join(skipped_no_fm)}", file=sys.stderr)

    return tickets


# ===== HTML 生成 =====

def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_status_legend() -> str:
    items = sorted(STATUS_CONFIG.items(), key=lambda x: x[1]["order"])
    parts = []
    for key, cfg in items:
        parts.append(
            f'<span class="legend-item" style="background:{cfg["bg"]};border-color:{cfg["border"]};color:{cfg["color"]}">'
            f'{escape_html(cfg["label"])}</span>'
        )
    return "\n".join(parts)


def render_ticket_card(ticket: dict) -> str:
    status = ticket["status"]
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["seed"])
    tags_html = ""
    if ticket["tags"]:
        tag_items = "".join(
            f'<span class="tag">{escape_html(t)}</span>' for t in ticket["tags"]
        )
        tags_html = f'<div class="tags">{tag_items}</div>'

    summary_html = ""
    if ticket["summary"]:
        summary_html = f'<p class="summary">{escape_html(ticket["summary"][:180])}</p>'

    date_html = ""
    if ticket["updated"]:
        date_html = f'<span class="date">更新: {escape_html(ticket["updated"])}</span>'

    return f"""
    <div class="card" style="border-left-color:{cfg["border"]}">
      <div class="card-header">
        <span class="status-badge" style="background:{cfg["bg"]};color:{cfg["color"]};border-color:{cfg["border"]}">{escape_html(cfg["label"])}</span>
        <span class="ticket-id">{escape_html(ticket["id"])}</span>
        {date_html}
      </div>
      <h3 class="card-title">{escape_html(ticket["title"])}</h3>
      {summary_html}
      {tags_html}
    </div>"""


def render_section(title: str, tickets: list[dict], section_id: str) -> str:
    if not tickets:
        return ""
    cards = "\n".join(render_ticket_card(t) for t in tickets)
    count = len(tickets)
    return f"""
  <section class="ticket-section" id="{escape_html(section_id)}">
    <h2 class="section-title">{escape_html(title)} <span class="count">({count})</span></h2>
    <div class="card-grid">
      {cards}
    </div>
  </section>"""


def generate_html(all_tickets: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # セクション分割
    in_progress = [t for t in all_tickets if t["status"] != "delivered"]
    completed = [t for t in all_tickets if t["status"] == "delivered"]

    # in_progress をステータス順にソート
    in_progress.sort(key=lambda t: STATUS_CONFIG.get(t["status"], {"order": 99})["order"])

    in_progress_html = render_section("進行中 / In Progress", in_progress, "in-progress")
    completed_html = render_section("完了 / Delivered", completed, "completed")
    legend_html = render_status_legend()

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NINJINE — 開発ロードマップ</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    /* ===== リセット & 変数 ===== */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #FAFAF8;
      --text: #2A2A2A;
      --text-muted: #6A6A6A;
      --border: #DDDBD5;
      --card-bg: #FFFFFF;
      --header-bg: #F0EDE5;
      --font: 'Noto Serif JP', 'Hiragino Mincho ProN', 'Yu Mincho', serif;
      --radius: 6px;
      --shadow: 0 1px 4px rgba(42,42,42,0.08);
    }}

    /* ===== ベース ===== */
    body {{
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      min-height: 100vh;
    }}

    a {{ color: inherit; text-decoration: underline; }}
    a:hover {{ opacity: 0.75; }}

    /* ===== ヘッダー ===== */
    .site-header {{
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      padding: 2rem 1.5rem 1.5rem;
      text-align: center;
    }}
    .site-header .logo {{
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: 0.15em;
      color: var(--text);
      text-decoration: none;
    }}
    .site-header h1 {{
      font-size: clamp(1.1rem, 4vw, 1.5rem);
      font-weight: 600;
      margin-top: 0.5rem;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }}
    .site-header .meta {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.4rem;
    }}
    .back-link {{
      display: inline-block;
      margin-top: 0.75rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      text-decoration: none;
      border: 1px solid var(--border);
      padding: 0.25rem 0.75rem;
      border-radius: var(--radius);
      transition: background 0.15s;
    }}
    .back-link:hover {{ background: var(--border); opacity: 1; }}

    /* ===== メインレイアウト ===== */
    main {{
      max-width: 900px;
      margin: 0 auto;
      padding: 2rem 1.25rem 4rem;
    }}

    /* ===== 凡例 ===== */
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 2.5rem;
      padding: 1rem 1.25rem;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
    }}
    .legend-title {{
      width: 100%;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 0.25rem;
    }}
    .legend-item {{
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.2rem 0.65rem;
      border-radius: 999px;
      border: 1px solid;
      letter-spacing: 0.03em;
    }}

    /* ===== セクション ===== */
    .ticket-section {{
      margin-bottom: 2.5rem;
    }}
    .section-title {{
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-bottom: 1rem;
      padding-bottom: 0.4rem;
      border-bottom: 2px solid var(--border);
      color: var(--text);
    }}
    .section-title .count {{
      font-size: 0.8rem;
      font-weight: 400;
      color: var(--text-muted);
    }}

    /* ===== カードグリッド ===== */
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1rem;
    }}
    @media (max-width: 540px) {{
      .card-grid {{ grid-template-columns: 1fr; }}
    }}

    /* ===== カード ===== */
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-left: 4px solid;
      border-radius: var(--radius);
      padding: 1rem 1.1rem;
      box-shadow: var(--shadow);
    }}
    .card-header {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.5rem;
    }}
    .status-badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      border: 1px solid;
      letter-spacing: 0.04em;
    }}
    .ticket-id {{
      font-size: 0.72rem;
      color: var(--text-muted);
      font-family: 'Courier New', monospace;
    }}
    .date {{
      font-size: 0.68rem;
      color: var(--text-muted);
      margin-left: auto;
    }}
    .card-title {{
      font-size: 0.92rem;
      font-weight: 600;
      line-height: 1.5;
      margin-bottom: 0.4rem;
    }}
    .summary {{
      font-size: 0.8rem;
      color: var(--text-muted);
      line-height: 1.6;
      margin-bottom: 0.5rem;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      margin-top: 0.5rem;
    }}
    .tag {{
      font-size: 0.65rem;
      background: #F0EDE5;
      color: var(--text-muted);
      padding: 0.1rem 0.45rem;
      border-radius: 3px;
      border: 1px solid var(--border);
    }}

    /* ===== ESHINE プレースホルダー ===== */
    .eshine-roadmap-section {{
      margin-bottom: 2.5rem;
      padding: 1.25rem;
      background: var(--card-bg);
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      text-align: center;
    }}
    .eshine-roadmap-section h2 {{
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }}
    .eshine-roadmap-placeholder {{
      min-height: 80px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      font-size: 0.78rem;
      /* ESHINE 製巻物ロードマップ画像をここに挿入 (v2) */
    }}

    /* ===== フッター ===== */
    .site-footer {{
      border-top: 1px solid var(--border);
      padding: 1.25rem 1.5rem;
      text-align: center;
      font-size: 0.78rem;
      color: var(--text-muted);
    }}
    .site-footer a {{
      color: var(--text-muted);
    }}
    .footer-links {{
      margin-bottom: 0.4rem;
    }}
    .footer-links a {{
      margin: 0 0.5rem;
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <a href="../" class="logo" aria-label="NINJINE トップページ">NINJINE</a>
    <h1>開発ロードマップ</h1>
    <p class="meta">Build in Public — 生成日時: {now}</p>
    <a href="../" class="back-link">← トップページへ</a>
  </header>

  <main>
    <!-- ===== ステータス凡例 ===== -->
    <div class="legend" role="complementary" aria-label="ステータス凡例">
      <p class="legend-title">ステータス凡例 / Status Legend</p>
      {legend_html}
    </div>

    <!-- ===== ESHINE ロードマップ画像プレースホルダー ===== -->
    <!-- ESHINE 製巻物ロードマップ画像統合予定 (v2) -->
    <section class="eshine-roadmap-section" aria-label="ESHINE ロードマップ統合予定">
      <h2>ESHINE ビジュアルロードマップ（準備中）</h2>
      <div class="eshine-roadmap-placeholder">
        <!-- ESHINE が生成した animated SVG ロードマップ巻物をここに配置 (v2) -->
        ESHINE 製ロードマップビジュアル（Coming Soon）
      </div>
    </section>

    {in_progress_html}
    {completed_html}
  </main>

  <footer class="site-footer">
    <div class="footer-links">
      <a href="../">トップページ</a>
      <a href="https://x.com/NINJINE000" target="_blank" rel="noopener">X @NINJINE000</a>
    </div>
    <p>© 2026 NINJINE — In development</p>
  </footer>
</body>
</html>"""


# ===== メイン =====

def main():
    print("=" * 50, file=sys.stderr)
    print("N-BIP-02: ロードマップ HTML 生成開始", file=sys.stderr)
    print(f"入力 (active): {ACTIVE_DIR}", file=sys.stderr)
    print(f"入力 (done):   {DONE_DIR}", file=sys.stderr)
    print(f"出力:          {OUTPUT_PATH}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # チケット読み込み
    active_tickets = load_tickets(ACTIVE_DIR)
    done_tickets = load_tickets(DONE_DIR)
    all_tickets = active_tickets + done_tickets

    print(f"\n[RESULT] 公開対象チケット合計: {len(all_tickets)} 件", file=sys.stderr)
    for t in all_tickets:
        print(f"  - {t['id']} [{t['status']}] {t['title'][:50]}", file=sys.stderr)

    # AC-3 確認: private チケットが含まれていないことをログで保証
    print(f"\n[AC-3 CHECK] public: true のチケットのみ出力対象。非公開チケットはすべてスキップ済み。", file=sys.stderr)

    # HTML 生成
    html = generate_html(all_tickets)

    # 出力ディレクトリ作成
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    print(f"\n[OK] 生成完了: {OUTPUT_PATH}", file=sys.stderr)
    print(f"[OK] チケット数: {len(all_tickets)} 件 (active: {len(active_tickets)}, done: {len(done_tickets)})", file=sys.stderr)
    print(f"\n公開 URL: https://joh-shimo-jp.github.io/ninjine-landing/roadmap/", file=sys.stderr)


if __name__ == "__main__":
    main()
