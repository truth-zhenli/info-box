#!/usr/bin/env python3
"""
⭐ 升级星星系统到 v13 — 目录权限 + 取消即删除
替换所有每日页面的 v12 星星脚本为 v13

改动：
1. showDirectoryPicker 替代 showSaveFilePicker（目录权限更稳定）
2. 取消星星 → 从 favorites.json 删除条目（不是标 false）
3. 保留其他页面的星标不受影响
4. papers.html PRERENDERED_COUNTS 正则支持任意年份
"""
import re, json
from pathlib import Path

REPO = Path("/mnt/d/LZ&AI/info-box")
PAPERS = REPO / "pages" / "papers"

# ========== 新的星星脚本 v13 ==========
STAR_JS_V13 = """<script>
/* 收藏功能 v13 -- 目录权限 + 取消即删除 */
(function(){
  var stars = document.querySelectorAll('.star-btn');
  if(!stars.length) return;

  var SAVE_DELAY = 2000;
  var saveTimer = null;
  var dirHandle = null;

  /* IndexedDB */
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
  function clearDB(){
    try { indexedDB.deleteDatabase('star-fav-dir'); } catch(e){}
  }
  function loadDirHandle(){
    return openDB().then(function(db){
      return new Promise(function(resolve){
        var tx = db.transaction('handles','readonly');
        var req = tx.objectStore('handles').get('fav-dir');
        req.onsuccess = function(){ resolve(req.result); };
        req.onerror = function(){ resolve(null); };
      });
    }).catch(function(){ return null; });
  }
  function saveDirHandle(handle){
    return openDB().then(function(db){
      return new Promise(function(resolve, reject){
        var tx = db.transaction('handles','readwrite');
        tx.objectStore('handles').put(handle, 'fav-dir');
        tx.oncomplete = resolve; tx.onerror = reject;
      });
    }).catch(function(){});
  }

  function readFavJson(){
    if(!dirHandle) return Promise.resolve([]);
    return dirHandle.getFileHandle('favorites.json')
      .then(function(fh){ return fh.getFile(); })
      .then(function(f){ return f.text(); })
      .then(function(t){ try{return JSON.parse(t);}catch(e){return [];} })
      .catch(function(){ return []; });
  }
  function writeFavJson(data){
    if(!dirHandle) return Promise.reject('no dir');
    return dirHandle.getFileHandle('favorites.json', {create: true})
      .then(function(fh){
        return fh.requestPermission({mode:'readwrite'}).then(function(p){
          if(p!=='granted') throw new Error('denied');
          return fh.createWritable();
        }).then(function(w){
          return w.write(JSON.stringify(data, null, 2)).then(function(){ return w.close(); });
        });
      });
  }

  function mergeStars(master){
    /* 逻辑：当前页点亮的保留，没点亮的删掉；其他页点亮的保留 */
    if(!Array.isArray(master)) master = [];
    var starredFromOther = {};
    master.forEach(function(i){ starredFromOther[i.title+'|||'+i.link] = i; });

    var result = [];
    var seenOnPage = {};

    stars.forEach(function(s){
      var k = s.dataset.title+'|||'+s.dataset.link;
      seenOnPage[k] = true;
      var isFav = s.textContent === '\\u2605';
      if(isFav){
        result.push({
          title: s.dataset.title,
          link: s.dataset.link,
          cnTitle: s.dataset.cn||'',
          journal: s.dataset.journal||'',
          authors: s.dataset.authors||'',
          date: s.dataset.date||'',
          starred: true
        });
      }
      /* 取消点亮 → 不加入result → 相当于从 favorites.json 删掉 */
    });

    /* 保留其他页面上仍然点亮的条目 */
    Object.keys(starredFromOther).forEach(function(k){
      if(!seenOnPage[k] && starredFromOther[k].starred){
        result.push(starredFromOther[k]);
      }
    });

    return result;
  }

  function doSave(){
    if(!dirHandle) return;
    readFavJson().then(function(ex){
      return writeFavJson(mergeStars(ex));
    }).catch(function(){
      dirHandle = null;
      clearDB();
    });
  }

  function setupHandle(){
    return window.showDirectoryPicker()
      .then(function(dir){
        dirHandle = dir;
        saveDirHandle(dir);
        return doSave();
      })
      .catch(function(e){
        if(e.name==='AbortError') return;
        fallback();
      });
  }

  function fallback(){
    var data = mergeStars([]);
    var json = JSON.stringify(data,null,2);
    var blob = new Blob([json],{type:'application/json;charset=utf-8'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'favorites.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){URL.revokeObjectURL(url);},2000);
    alert('请将下载的 favorites.json 保存到 D:\\\\LZ&AI\\\\info-box\\\\ 目录下覆盖原文件');
  }

  function applyStar(star, isFav){
    star.textContent = isFav ? '\\u2605' : '\\u2606';
    star.style.color = isFav ? '#f5a623' : '#ccc';
    star.style.textShadow = isFav ? '0 0 4px rgba(245,166,35,0.5)' : 'none';
    star.title = isFav ? '已收藏' : '点击收藏';
  }

  /* 恢复星星 */
  stars.forEach(function(star,i){
    var key='fav_'+star.dataset.date+'_'+i;
    var st=(function(){try{return JSON.parse(localStorage.getItem(key));}catch(e){return null;}})();
    if(st&&st.title===star.dataset.title){applyStar(star,st.starred!==false);}
    else{applyStar(star,(star.getAttribute('data-star')||'')==='\\u2605');}
  });

  /* 加载目录句柄，同步 favorites.json → 页面 */
  loadDirHandle().then(function(dir){
    if(!dir) return;
    dirHandle = dir;
    readFavJson().then(function(ex){
      var map = {}; ex.forEach(function(i){ map[i.title+'|||'+i.link] = i; });
      stars.forEach(function(star,i){
        var k = star.dataset.title+'|||'+star.dataset.link;
        if(map[k] && map[k].starred){
          applyStar(star, true);
          var lk = 'fav_'+star.dataset.date+'_'+i;
          localStorage.setItem(lk, JSON.stringify(map[k]));
        }
      });
    }).catch(function(){});
  });

  /* 绑定点击 */
  stars.forEach(function(star,i){
    star.onclick=function(e){
      e.stopPropagation();e.preventDefault();
      var wasFav=star.textContent==='\\u2605';
      applyStar(star,!wasFav);
      var key='fav_'+star.dataset.date+'_'+i;
      if(wasFav) localStorage.removeItem(key);
      else localStorage.setItem(key,JSON.stringify({title:star.dataset.title,link:star.dataset.link,cn:star.dataset.cn,journal:star.dataset.journal,authors:star.dataset.authors,date:star.dataset.date,starred:true}));

      if(!dirHandle && window.showDirectoryPicker){ setupHandle(); return; }
      if(!dirHandle){ fallback(); return; }
      if(saveTimer) clearTimeout(saveTimer);
      saveTimer=setTimeout(doSave,SAVE_DELAY);
    };
  });
  console.log('\\u2b50 v13');
})();
</script>"""


def extract_old_star_script(content):
    """Extract the existing star script from HTML content.
    Handles: 收藏功能 v12, ★ 收藏功能 v12, and unicode-escaped versions."""
    # Strategy: find a <script> block that contains star-btn references
    # and has a version marker like v12, v13
    m = re.search(
        r'<script>(?:(?!</script>).)*?收藏功能 v\d+.*?</script>',
        content, re.DOTALL
    )
    if not m:
        # Try unicode-escaped version
        m = re.search(
            r'<script>(?:(?!</script>).)*?v\d+.*?document\.querySelectorAll.*?star-btn.*?</script>',
            content, re.DOTALL
        )
    return m.group(0) if m else None


def update_html_file(html_path):
    """Replace the star script in a daily HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_script = extract_old_star_script(content)
    if not old_script:
        # Maybe already v13 — check for the new script marker
        if '收藏功能 v13' in content:
            return 'already_v13'
        return 'no_star_script'

    # Replace
    new_content = content.replace(old_script, STAR_JS_V13, 1)
    if new_content == content:
        return 'no_change'

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return 'updated'


def update_papers_html():
    """Fix the PRERENDERED_COUNTS regex to handle any year dynamically."""
    papers_path = REPO / "pages" / "papers.html"
    if not papers_path.exists():
        return

    # Read current favorites.json
    fav_path = REPO / "favorites.json"
    fav_data = []
    if fav_path.exists():
        with open(fav_path, 'r', encoding='utf-8') as f:
            fav_data = json.load(f)

    from collections import defaultdict
    year_counts = defaultdict(lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    for p in fav_data:
        if not p.get("starred") or not p.get("date"):
            continue
        y = p["date"].split("-")[0]
        m = int(p["date"].split("-")[1])
        qq = 1 if m <= 3 else 2 if m <= 6 else 3 if m <= 9 else 4
        year_counts[y][qq] += 1

    # Build multi-year object: {2026:{1:0,2:1,3:0,4:0}, 2025:{...}}
    year_parts = []
    for y in sorted(year_counts.keys()):
        q_pairs = ",".join(f"{k}:{year_counts[y][k]}" for k in sorted(year_counts[y].keys()))
        year_parts.append(f"{y}:{{{q_pairs}}}")
    new_str = "var PRERENDERED_COUNTS = {" + ",".join(year_parts) + "};"

    with open(papers_path, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    # Replace the existing PRERENDERED_COUNTS line (handles any year)
    pattern = r'var PRERENDERED_COUNTS = \{.*?\};'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        content = re.sub(pattern, new_str, content, count=1)
    else:
        # Insert after the QUARTERS definition
        content = content.replace(
            "const QUARTERS = [",
            f"{new_str}\n\nconst QUARTERS = [",
            1
        )

    if content != orig:
        with open(papers_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 'updated'
    return 'no_change'


def main():
    # 1. Update all daily HTML pages
    html_files = sorted(PAPERS.rglob("????/??/????-??-??.html"))
    print(f"📄 扫描到 {len(html_files)} 个每日页面")

    stats = {"updated": 0, "already_v13": 0, "no_star_script": 0, "no_change": 0}
    for f in html_files:
        result = update_html_file(f)
        stats[result] = stats.get(result, 0) + 1
        if result == 'updated':
            print(f"  ✏️ {f.name}")

    print(f"\n✅ 更新: {stats['updated']}, 已是v13: {stats['already_v13']}, 无星星脚本: {stats['no_star_script']}")

    # 2. Update papers.html
    pr = update_papers_html()
    print(f"📊 papers.html: {pr}")

    # 3. Run gen_quarterly.py to regenerate all Q1-Q4
    import subprocess
    result = subprocess.run(
        ["python3", str(REPO / "scripts" / "gen_quarterly.py")],
        capture_output=True, text=True, cwd=str(REPO)
    )
    print(f"\n📊 gen_quarterly.py 输出:")
    for line in result.stdout.strip().split("\n"):
        print(f"  {line}")
    if result.stderr.strip():
        print(f"  ⚠️ {result.stderr.strip()}")

    print("\n🎉 完成！")


if __name__ == "__main__":
    main()
