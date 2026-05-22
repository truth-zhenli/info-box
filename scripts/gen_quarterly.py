#!/usr/bin/env python3
"""Generate quarterly精选 pages — localStorage + GitHub API + raw fallback."""

import os, json

BASE = "/home/administrator/info-box"

quarters = [
    {"q": 1, "emoji": "🌸", "label": "一季度", "months": [1,2,3], "color": "#e91e63", "bg": "linear-gradient(135deg,#c2185b 0%,#e91e63 100%)", "monthNames": "1月 · 2月 · 3月"},
    {"q": 2, "emoji": "☀️", "label": "二季度", "months": [4,5,6], "color": "#ff6f00", "bg": "linear-gradient(135deg,#e65100 0%,#ff6f00 100%)", "monthNames": "4月 · 5月 · 6月"},
    {"q": 3, "emoji": "🍂", "label": "三季度", "months": [7,8,9], "color": "#2e7d32", "bg": "linear-gradient(135deg,#1b5e20 0%,#2e7d32 100%)", "monthNames": "7月 · 8月 · 9月"},
    {"q": 4, "emoji": "❄️", "label": "四季度", "months": [10,11,12], "color": "#1565c0", "bg": "linear-gradient(135deg,#0d47a1 0%,#1565c0 100%)", "monthNames": "10月 · 11月 · 12月"},
]

for q in quarters:
    qi = q["q"]
    months_json = json.dumps(q["months"])
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{q["emoji"]} 2026年{q["label"]}精选 - 碎片化信息盒</title>
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
.loading{{text-align:center;color:#aaa;font-size:14px;padding:40px 0}}
.footer{{text-align:center;color:#ccc;font-size:12px;margin-top:30px}}
@media (max-width:480px){{body{{padding:12px 10px}}.header{{padding:16px 16px}}.header h1{{font-size:17px}}.nav-bar{{padding:8px 6px}}.nav-link{{font-size:11px;padding:5px 7px}}.paper-card{{padding:14px 14px}}}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>{q["emoji"]} 2026年{q["label"]}精选</h1>
  <div class="sub">{q["monthNames"]} — 实时加载你收藏的好文章</div>
</div>
<div class="nav-bar">
    <a class="nav-link" href="../碎片化信息盒.html">🏠 首页</a>
    <a class="nav-link" href="文献追踪.html">📰 文献追踪</a>
    <a class="nav-link {"active" if qi==1 else ""}" href="1季度精选.html">🌸 Q1</a>
    <a class="nav-link {"active" if qi==2 else ""}" href="2季度精选.html">☀️ Q2</a>
    <a class="nav-link {"active" if qi==3 else ""}" href="3季度精选.html">🍂 Q3</a>
    <a class="nav-link {"active" if qi==4 else ""}" href="4季度精选.html">❄️ Q4</a>
  </div>
<div id="list"><div class="loading">⏳ 加载收藏数据...</div></div>
<div class="footer">localStorage即时 + GitHub双fallback</div>
</div>
<script>
(function(){{
  var listEl = document.getElementById('list');
  var quarter = {qi};
  var allowedMonths = {months_json};
  var paperMap = {{}};
  var rendered = false;

  function render(papers){{
    var keys = Object.keys(papers);
    if(keys.length === 0) return;
    rendered = true;
    var sorted = keys.sort(function(a,b){{
      return papers[b].date.localeCompare(papers[a].date);
    }});
    var html = '';
    sorted.forEach(function(k){{
      var p = papers[k];
      html += '<div class="paper-card">';
      html += '<div class="paper-title"><a href="' + p.link + '" target="_blank">' + p.title + '</a></div>';
      if(p.cnTitle) html += '<div class="paper-cn">' + p.cnTitle + '</div>';
      if(p.journal) html += '<div class="paper-meta"><span class="meta-tag">' + p.journal + '</span></div>';
      if(p.authors) html += '<div class="paper-authors">' + p.authors + '</div>';
      html += '<div class="paper-date">📅 ' + p.date + '</div>';
      html += '</div>';
    }});
    listEl.innerHTML = html;
  }}

  function processFavs(favs){{
    var changed = false;
    favs.forEach(function(p){{
      if(!p.starred || !p.date) return;
      var m = parseInt(p.date.split('-')[1]);
      if(allowedMonths.indexOf(m) < 0) return;
      var uid = p.title + '|||' + p.link;
      if(!paperMap[uid]){{
        paperMap[uid] = {{
          title: p.title, link: p.link,
          cnTitle: p.cnTitle || '', journal: p.journal || '',
          authors: p.authors || '', date: p.date
        }};
        changed = true;
      }}
    }});
    if(changed || !rendered) render(paperMap);
    if(Object.keys(paperMap).length === 0 && !rendered){{
      listEl.innerHTML = '<div class="empty-tip"><span class="big">🌟</span>还没有收藏的文章<br>在文献阅读页面点击☆收藏，就会出现在这里</div>';
    }}
  }}

  /* 第一步：从 localStorage 读取（即时！） */
  for(var i = 0; i < localStorage.length; i++){{
    var key = localStorage.key(i);
    if(key && key.indexOf('fav_') === 0){{
      try{{
        var val = JSON.parse(localStorage.getItem(key));
        if(val && val.title && val.date){{
          var m = parseInt(val.date.split('-')[1]);
          if(allowedMonths.indexOf(m) >= 0){{
            var uid = val.title + '|||' + val.link;
            paperMap[uid] = {{
              title: val.title, link: val.link,
              cnTitle: val.cnTitle || '', journal: val.journal || '',
              authors: val.authors || '', date: val.date
            }};
          }}
        }}
      }}catch(e){{}}
    }}
  }}
  render(paperMap);

  /* 第二步：从 GitHub API 读取（跨设备持久化，无CDN缓存） */
  function fetchAndParse(url, cb){{
    fetch(url + '?t=' + new Date().getTime())
      .then(function(r){{ return r.json(); }})
      .then(cb)
      .catch(function(){{}});
  }}
  fetchAndParse('https://api.github.com/repos/truth-zhenli/info-box/contents/favorites.json', function(data){{
    try {{ processFavs(JSON.parse(decodeURIComponent(escape(atob(data.content))))); }} catch(e){{}}
  }});
  /* 靠后fallback：raw CDN */
  setTimeout(function(){{
    fetchAndParse('https://raw.githubusercontent.com/truth-zhenli/info-box/main/favorites.json', processFavs);
  }}, 500);
}})();
</script>
</body>
</html>'''

    out_path = os.path.join(BASE, "页面", f"{qi}季度精选.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ {qi}季度精选.html")

print("\nDone! localStorage → GitHub API → raw fallback")