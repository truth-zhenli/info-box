#!/usr/bin/env python3
"""Generate quarterly精选 pages from favorites.json — run after updating favorites"""

import json, os

BASE = "/home/administrator/info-box"
with open(os.path.join(BASE, "favorites.json")) as f:
    favorites = json.load(f)

# Only favorited papers
favs = [p for p in favorites if p.get("starred")]

# Quarterly config
quarters = [
    {"q": 1, "emoji": "🌸", "label": "一季度", "months": [1,2,3], "color": "#e91e63", "bg": "linear-gradient(135deg,#c2185b 0%,#e91e63 100%)"},
    {"q": 2, "emoji": "☀️", "label": "二季度", "months": [4,5,6], "color": "#ff6f00", "bg": "linear-gradient(135deg,#e65100 0%,#ff6f00 100%)"},
    {"q": 3, "emoji": "🍂", "label": "三季度", "months": [7,8,9], "color": "#2e7d32", "bg": "linear-gradient(135deg,#1b5e20 0%,#2e7d32 100%)"},
    {"q": 4, "emoji": "❄️", "label": "四季度", "months": [10,11,12], "color": "#1565c0", "bg": "linear-gradient(135deg,#0d47a1 0%,#1565c0 100%)"},
]

q_names = ["一", "二", "三", "四"]

for qi, q in enumerate(quarters):
    # Filter papers for this quarter
    q_papers = [p for p in favs if p.get("date") and int(p["date"].split("-")[1]) in q["months"]]
    q_papers.sort(key=lambda x: x.get("date", ""), reverse=True)

    active_nav = qi + 1

    cards_html = ""
    if not q_papers:
        cards_html = '<div class="empty-tip"><span class="big">🌟</span>还没有收藏的文章<br>在文献阅读页面点击☆收藏，就会出现在这里</div>'
    else:
        for p in q_papers:
            link = p.get("link", "#")
            title = p.get("title", "")
            journal = p.get("journal", "")
            authors = p.get("authors", "")
            date = p.get("date", "")
            cn = p.get("cnTitle", "")
            cards_html += f'''<div class="paper-card">
<div class="paper-title"><a href="{link}" target="_blank">{title}</a></div>
<div class="paper-cn">{cn}</div>
<div class="paper-meta"><span class="meta-tag">{journal}</span></div>
<div class="paper-authors">{authors}</div>
<div class="paper-date">📅 {date}</div>
</div>
'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{q["emoji"]} {q["label"]}精选 - 碎片化信息盒</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f0eb;color:#333;line-height:1.8;padding:30px 20px}}
.container{{max-width:900px;margin:0 auto}}
.header{{background:{q["bg"]};color:#fff;padding:22px 26px;border-radius:14px;margin-bottom:18px}}
.header h1{{font-size:20px;font-weight:700}}
.header .sub{{font-size:13px;opacity:.7;margin-top:3px}}
.nav-bar{{background:#fff;border-radius:10px;padding:10px 14px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);display:flex;flex-wrap:wrap;gap:3px;justify-content:center}}
.nav-link{{display:inline-block;padding:5px 10px;border-radius:6px;font-size:12px;text-decoration:none;color:#555;transition:all .15s;white-space:nowrap}}
.nav-link:hover{{background:#eef2f7;color:#1a1a2e}}
.nav-link.active{{background:{q["color"]};color:#fff;font-weight:600}}
.empty-tip{{text-align:center;color:#ccc;font-size:14px;padding:60px 0}}
.empty-tip .big{{font-size:48px;display:block;margin-bottom:12px}}
.paper-card{{background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:4px solid {q["color"]}}}
.paper-title{{font-size:14px;font-weight:600;color:#0f3460;margin-bottom:4px}}
.paper-title a{{color:#0f3460;text-decoration:none}}
.paper-title a:hover{{text-decoration:underline}}
.paper-cn{{font-size:12px;color:#666;margin-bottom:6px}}
.paper-meta{{font-size:11px;color:#888;margin-bottom:4px;display:flex;flex-wrap:wrap;gap:4px}}
.meta-tag{{display:inline-block;background:#fce4ec;color:{q["color"]};padding:2px 8px;border-radius:8px;font-size:11px}}
.paper-authors{{font-size:11px;color:#999;margin-bottom:2px}}
.paper-date{{font-size:11px;color:#aaa}}
.footer{{text-align:center;color:#ccc;font-size:12px;margin-top:30px}}
@media (max-width:480px){{body{{padding:12px 10px}}.header{{padding:16px 16px}}.header h1{{font-size:17px}}.nav-bar{{padding:8px 6px}}.nav-link{{font-size:11px;padding:5px 7px}}.paper-card{{padding:14px 14px}}}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>{q["emoji"]} 2026年{q["label"]}精选</h1>
  <div class="sub">{" · ".join([str(m)+"月" for m in q["months"]])} — 你收藏的好文章</div>
</div>
<div class="nav-bar">
    <a class="nav-link" href="../碎片化信息盒.html">🏠 首页</a>
    <a class="nav-link" href="文献追踪.html">📰 文献追踪</a>
    {"".join([f'<a class="nav-link {"active" if i+1==qi+1 else ""}" href="{i+1}季度精选.html">{emoji} Q{i+1}</a>' for i, emoji in enumerate(["🌸","☀️","🍂","❄️"])])}
  </div>
<div id="list">{cards_html}</div>
<div class="footer">收藏的数据来源于 favorites.json 文件，刷新不丢失</div>
</div>
</body>
</html>'''

    out_path = os.path.join(BASE, "页面", f"{q['q']}季度精选.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ Generated {q['q']}季度精选.html ({len(q_papers)} papers)")

print("Done! All quarterly pages regenerated.")
