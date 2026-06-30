#!/usr/bin/env python3
"""Generate quarterly 精选 pages — pre-rendered from favorites.json.

Strategy: embed paper data directly in HTML so no XHR/fetch needed for local use.
Also keep localStorage reading for real-time updates after clicking stars,
and fetch as fallback for GitHub Pages online.

Uses .replace() for template variables instead of f-string to avoid
JavaScript braces conflicting with Python f-string syntax.
"""
import os, json
from datetime import datetime

BASE = "/mnt/d/LZ&AI/info-box"

quarters = [
    {"q": 1, "emoji": "🌸", "label": "一季度", "months": [1,2,3], "color": "#e91e63", "bg": "linear-gradient(135deg,#c2185b 0%,#e91e63 100%)", "monthNames": "1月 · 2月 · 3月"},
    {"q": 2, "emoji": "☀️", "label": "二季度", "months": [4,5,6], "color": "#ff6f00", "bg": "linear-gradient(135deg,#e65100 0%,#ff6f00 100%)", "monthNames": "4月 · 5月 · 6月"},
    {"q": 3, "emoji": "🍂", "label": "三季度", "months": [7,8,9], "color": "#2e7d32", "bg": "linear-gradient(135deg,#1b5e20 0%,#2e7d32 100%)", "monthNames": "7月 · 8月 · 9月"},
    {"q": 4, "emoji": "❄️", "label": "四季度", "months": [10,11,12], "color": "#1565c0", "bg": "linear-gradient(135deg,#0d47a1 0%,#1565c0 100%)", "monthNames": "10月 · 11月 · 12月"},
]

# Load favorites
fav_path = os.path.join(BASE, "favorites.json")
fav_data = []
if os.path.exists(fav_path):
    with open(fav_path, "r", encoding="utf-8") as f:
        fav_data = json.load(f)

def escape_js(s):
    """Escape string for embedding in JS string literal."""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")

# JS template — uses __VARS__ placeholders replaced below
# NOT an f-string, so JS braces are literal
JS_SCRIPT = """<script>
// 季度精选 — 实时读 favorites.json + 预渲染兜底
(function(){
  var MONTHS = __ALLOWED_MONTHS__;
  var listEl = document.getElementById('list');
  if(!listEl) return;

  function renderFromFavs(all){
    var papers = all.filter(function(p){ return p.starred && p.date; })
                    .filter(function(p){ var m=parseInt(p.date.split('-')[1]); return MONTHS.indexOf(m) >= 0; });
    if(papers.length === 0){
      listEl.innerHTML = '<div class=\"empty-tip\"><span class=\"big\">🌟</span>还没有收藏的文章<br>在文献页面点击☆收藏，这里就会出现</div>';
      return;
    }
    papers.sort(function(a,b){ return a.date < b.date ? 1 : -1; });
    var html = '';
    papers.forEach(function(p){
      var m = parseInt((p.date||'').split('-')[1]);
      if(!m) return;
      html += '<div class="paper-card">';
      html += '<div class="paper-month-tag">' + m + '\\u6708</div>';
      html += '<div class="paper-title"><a href="' + escAttr(p.link) + '" target="_blank">' + escHtml(p.title) + '</a></div>';
      if(p.cnTitle) html += '<div class="paper-cn">' + escHtml(p.cnTitle) + '</div>';
      if(p.journal) html += '<div class="paper-meta"><span class="meta-tag">' + escHtml(p.journal) + '</span></div>';
      if(p.authors) html += '<div class="paper-authors">' + escHtml(p.authors) + '</div>';
      html += '<div class="paper-date">\\ud83d\\udcc5 ' + (p.date||'') + '</div>';
      html += '</div>';
    });
    listEl.innerHTML = html;
  }

  function escHtml(s){
    if(!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function escAttr(s){
    if(!s) return '';
    return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // 通过目录句柄读 favorites.json（file:// 下 XHR 被禁，但目录句柄可用）
  function openDB(){
    return new Promise(function(res, rej){
      var req = indexedDB.open('star-fav-dir', 1);
      req.onupgradeneeded = function(e){
        var db = e.target.result;
        if(!db.objectStoreNames.contains('handles')) db.createObjectStore('handles');
      };
      req.onsuccess = function(e){ res(e.target.result); };
      req.onerror = function(e){ rej(e.target.error); };
    });
  }

  function readFav(){
    return openDB().then(function(db){
      return new Promise(function(resolve){
        var tx = db.transaction('handles','readonly');
        var req = tx.objectStore('handles').get('fav-dir');
        req.onsuccess = function(){ resolve(req.result); };
        req.onerror = function(){ resolve(null); };
      });
    }).then(function(dir){
      if(!dir) return null;
      return dir.getFileHandle('favorites.json')
        .then(function(fh){ return fh.getFile(); })
        .then(function(f){ return f.text(); })
        .then(function(t){ try{return JSON.parse(t);}catch(e){return null;} })
        .catch(function(){ return null; });
    }).catch(function(){ return null; });
  }

  readFav().then(function(data){
    if(data && Array.isArray(data)) renderFromFavs(data);
  });
})();
</script>"""

BASE_HTML_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__EMOJI__ __YEAR__年__LABEL__精选 - 碎片化信息盒</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f0eb;color:#333;line-height:1.8;padding:30px 20px}
.container{max-width:900px;margin:0 auto}
.header{background:__HEADER_BG__;color:#fff;padding:22px 26px;border-radius:14px;margin-bottom:18px}
.header h1{font-size:20px;font-weight:700}
.header .sub{font-size:13px;opacity:.7;margin-top:3px}
.nav-bar{background:#fff;border-radius:10px;padding:10px 14px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);display:flex;flex-wrap:wrap;gap:3px;justify-content:center}
.nav-link{display:inline-block;padding:5px 10px;border-radius:6px;font-size:12px;text-decoration:none;color:#555;transition:all .15s;white-space:nowrap}
.nav-link:hover{background:#eef2f7;color:#1a1a2e}
.nav-link.active{background:__ACTIVE_COLOR__;color:#fff;font-weight:600}
.empty-tip{text-align:center;color:#ccc;font-size:14px;padding:60px 0}
.empty-tip .big{font-size:48px;display:block;margin-bottom:12px}
.paper-card{background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:4px solid __ACTIVE_COLOR__;position:relative}
.paper-month-tag{position:absolute;top:12px;right:12px;background:__ACTIVE_COLOR__;color:#fff;font-size:11px;padding:2px 8px;border-radius:8px}
.paper-title{font-size:14px;font-weight:600;color:#0f3460;margin-bottom:4px;padding-right:60px}
.paper-title a{color:#0f3460;text-decoration:none}
.paper-title a:hover{text-decoration:underline}
.paper-cn{font-size:12px;color:#666;margin-bottom:6px}
.paper-meta{font-size:11px;color:#888;margin-bottom:4px;display:flex;flex-wrap:wrap;gap:4px}
.meta-tag{display:inline-block;background:#fce4ec;color:__ACTIVE_COLOR__;padding:2px 8px;border-radius:8px;font-size:11px}
.paper-authors{font-size:11px;color:#999;margin-bottom:2px}
.paper-date{font-size:11px;color:#aaa}
.footer{text-align:center;color:#ccc;font-size:12px;margin-top:30px}
@media (max-width:480px){body{padding:12px 10px}.header{padding:16px 16px}.header h1{font-size:17px}.nav-bar{padding:8px 6px}.nav-link{font-size:11px;padding:5px 7px}.paper-card{padding:14px 14px}.paper-title{padding-right:50px}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>__EMOJI__ __YEAR__年__LABEL__精选</h1>
  <div class="sub">__MONTH_NAMES__</div>
</div>
<div class="nav-bar">
    <a class="nav-link" href="../../../../index.html">🏠 首页</a>
    <a class="nav-link" href="../../../papers.html">📰 文献追踪</a>
__NAV_LINKS__
  </div>
<div id="list">__CARDS_HTML__</div>
<div class="footer">预渲染版 · 点星星后刷新页面即可更新</div>
</div>
__JS_SCRIPT__
</body>
</html>"""

def make_nav_links(current_qi, year):
    lines = []
    for q in quarters:
        qi = q["q"]
        active = ' active' if qi == current_qi else ''
        lines.append(f'    <a class="nav-link{active}" href="q{qi}.html">{q["emoji"]} {q["label"]}</a>')
    return '\n'.join(lines)

year = datetime.now().year

for q in quarters:
    qi = q["q"]
    months = q["months"]
    # Filter starred papers for this quarter
    papers = [p for p in fav_data if p.get("starred") and p.get("date")]
    papers = [p for p in papers if int(p["date"].split("-")[1]) in months]

    # Build paper cards HTML
    if papers:
        papers_sorted = sorted(papers, key=lambda p: p["date"], reverse=True)
        cards_parts = []
        for p in papers_sorted:
            m = int(p["date"].split("-")[1])
            title = escape_js(p.get("title", ""))
            link = escape_js(p.get("link", ""))
            cn = escape_js(p.get("cnTitle", ""))
            journal = escape_js(p.get("journal", ""))
            authors = escape_js(p.get("authors", ""))
            date = p.get("date", "")
            cards_parts.append(f'''<div class="paper-card">
    <div class="paper-month-tag">{m}月</div>
    <div class="paper-title"><a href="{link}" target="_blank">{title}</a></div>
    <div class="paper-cn">{cn}</div>
    <div class="paper-meta"><span class="meta-tag">{journal}</span></div>
    <div class="paper-authors">{authors}</div>
    <div class="paper-date">📅 {date}</div>
  </div>''')
        cards_html = '\n'.join(cards_parts)
    else:
        cards_html = '<div class="empty-tip"><span class="big">🌟</span>还没有收藏的文章<br>在文献页面点击☆收藏，这里就会出现</div>'

    # Build JS with substitutions
    allowed_months_js = json.dumps(months)
    nav_links = make_nav_links(qi, year)
    js = JS_SCRIPT.replace("__ALLOWED_MONTHS__", allowed_months_js)

    # Build full page
    html = BASE_HTML_TPL
    html = html.replace("__EMOJI__", q["emoji"])
    html = html.replace("__YEAR__", str(year))
    html = html.replace("__LABEL__", q["label"])
    html = html.replace("__MONTH_NAMES__", q["monthNames"])
    html = html.replace("__HEADER_BG__", q["bg"])
    html = html.replace("__ACTIVE_COLOR__", q["color"])
    html = html.replace("__NAV_LINKS__", nav_links)
    html = html.replace("__CARDS_HTML__", cards_html)
    html = html.replace("__JS_SCRIPT__", js)

    out_path = os.path.join(BASE, "pages", "papers", str(year), "fav", f"q{qi}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ q{qi}.html ({len(papers)} 篇收藏)")

# Update papers.html PRERENDERED_COUNTS
papers_path = os.path.join(BASE, "pages", "papers.html")
if os.path.exists(papers_path):
    with open(papers_path, "r", encoding="utf-8") as f:
        papers_html = f.read()

    import re
    from collections import defaultdict
    year_counts = defaultdict(lambda: {1:0, 2:0, 3:0, 4:0})
    for p in fav_data:
        if not p.get("starred") or not p.get("date"):
            continue
        y = p["date"].split("-")[0]
        m = int(p["date"].split("-")[1])
        qq = 1 if m <= 3 else 2 if m <= 6 else 3 if m <= 9 else 4
        year_counts[y][qq] += 1

    # Build {2026:{1:0,2:5,3:0,4:0}} format
    year_pairs = []
    for y in sorted(year_counts.keys()):
        q_pairs = ",".join(f"{k}:{year_counts[y][k]}" for k in sorted(year_counts[y].keys()))
        year_pairs.append(f"{y}:{{{q_pairs}}}")
    new_str = "{" + ",".join(year_pairs) + "}"

    # Replace __PRERENDERED_COUNTS_JSON__ placeholder with actual data
    papers_html = papers_html.replace(
        "__PRERENDERED_COUNTS_JSON__", new_str, 1
    )
    # Also handle the case where placeholder was already replaced (regex fallback)
    if "__PRERENDERED_COUNTS_JSON__" not in papers_html:
        import re
        papers_html = re.sub(
            r'var PRERENDERED_COUNTS = \{.*?\};?',
            f"var PRERENDERED_COUNTS = {new_str};",
            papers_html, count=1
        )
    with open(papers_path, "w", encoding="utf-8") as f:
        f.write(papers_html)
    print(f"✓ papers.html 计数已更新: { {y: dict(year_counts[y]) for y in sorted(year_counts.keys())} }")

print("\nDone! 预渲染版季度精选已生成 ✅")
