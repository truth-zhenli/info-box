#!/usr/bin/env python3
"""
⭐ Star Syncer — 读取 Resilio Sync 同步来的 favorites.json，
   与 git HEAD 版本合并（HEAD为主，新收藏叠加），
   更新所有 HTML 星星状态，重新生成季度精选。
   
   重要：不修改 WSL 上的 favorites.json（避免与 Resilio Sync 冲突）
"""
import json
import subprocess
import sys
import re
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
FAV_JSON = REPO_DIR / "favorites.json"
PAPERS_DIR = REPO_DIR / "pages" / "papers"

def get_git_head_favs():
    try:
        out = subprocess.check_output(
            ["git", "show", "HEAD:favorites.json"],
            cwd=str(REPO_DIR), stderr=subprocess.DEVNULL
        )
        return json.loads(out)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []

def get_disk_favs():
    if not FAV_JSON.exists():
        return []
    with open(FAV_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def merge_favs(head, disk):
    """HEAD为主，disk中新收藏叠加"""
    head_idx = {i["title"] + "|||" + i["link"]: i for i in head}
    disk_idx = {i["title"] + "|||" + i["link"]: i for i in disk}
    
    merged = []
    for key, item in head_idx.items():
        if key in disk_idx and disk_idx[key].get("starred"):
            item["starred"] = True
        merged.append(item)
    
    seen = {i["title"] + "|||" + i["link"] for i in merged}
    for key, item in disk_idx.items():
        if key not in seen:
            merged.append(item)
            seen.add(key)
    
    return merged

def get_html_files():
    """扫描所有日期HTML文件"""
    files = []
    # 扫描 pages/papers/YYYY/MM/YYYY-MM-DD.html
    for f in sorted(PAPERS_DIR.rglob("????/??/????-??-??.html")):
        if f.suffix == ".html":
            files.append(f)
    # 也扫描平铺的旧路径
    for f in sorted(PAPERS_DIR.parent.glob("????-??-??.html")):
        if f.name not in [p.name for p in files]:
            files.append(f)
    return files

def update_html_stars(html_path, fav_map):
    """在 HTML 中更新 data-star 属性"""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    orig = content
    for link, should_star in fav_map.items():
        if link not in content:
            continue
        
        idx = content.find(link)
        star_start = content.rfind('<span class="star-btn"', 0, idx)
        if star_start == -1:
            continue
        
        star_end = content.find("</span>", star_start)
        block = content[star_start:star_end]
        
        new_char = "★" if should_star else "☆"
        
        # 替换 data-star 属性值
        if 'data-star="★"' in block:
            content = content[:star_start] + block.replace('data-star="★"', f'data-star="{new_char}"') + content[star_end:]
        elif 'data-star="☆"' in block:
            content = content[:star_start] + block.replace('data-star="☆"', f'data-star="{new_char}"') + content[star_end:]
        
        # 替换显示字符（>★< 或 >☆<）
        star_end2 = content.find("</span>", star_start)
        block2 = content[star_start:star_end2]
        last_gt = block2.rfind(">")
        old_d = block2[last_gt+1:]
        if old_d in ("★", "☆"):
            content = content[:star_start+last_gt+1] + new_char + content[star_start+last_gt+2:]
    
    if content != orig:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, len(re.findall(r'data-star="★"', content))
    return False, len(re.findall(r'data-star="★"', content))

def update_papers_html_count():
    """更新 papers.html 中的论文统计计数"""
    papers_file = REPO_DIR / "pages" / "papers.html"
    if not papers_file.exists():
        return
    
    # 读取所有日期页面，统计每页论文数
    date_counts = {}
    for f in sorted(PAPERS_DIR.rglob("????/??/????-??-??.html")):
        if f.suffix != ".html":
            continue
        date_str = f.stem  # YYYY-MM-DD
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
        # 统计论文卡片数：通过 star-btn 数量
        count = content.count('<span class="star-btn"')
        date_counts[date_str] = count
    
    with open(papers_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    orig = content
    for date_str, count in date_counts.items():
        # 更新 papers:X 字段
        old = f'date:"{date_str}", title:"', 
        pattern = rf'date:"{re.escape(date_str)}",[^}}]*papers:(\d+)'
        m = re.search(pattern, content)
        if m and int(m.group(1)) != count:
            content = content.replace(
                f'date:"{date_str}", title:"',
                f'date:"{date_str}", papers:{count}, title:"',
                1
            ) if 'papers:' not in content[content.find(f'date:"{date_str}"'):content.find(f'date:"{date_str}"')+80] else content
    
    if content != orig:
        # Simple approach: just find and replace the papers count
        pass  # Skip for now - papers count is a nice-to-have

def main():
    print("=" * 40)
    print("⭐ Star Syncer")
    print("=" * 40)
    
    head = get_git_head_favs()
    disk = get_disk_favs()
    
    print(f"📖 git HEAD: {len(head)} 条")
    print(f"📖 工作副本: {len(disk)} 条")
    
    if not head and not disk:
        print("❌ 无可用的 favorites.json")
        return
    
    merged = merge_favs(head, disk)
    starred = [i for i in merged if i.get("starred")]
    print(f"📝 合并: {len(merged)} 条, 收藏 {len(starred)} 篇")
    for s in starred:
        print(f"  ✅ {s['date']} | {s['title'][:55]}")
    
    # 构建收藏 map
    fav_map = {item["link"]: item.get("starred", False) for item in merged}
    
    # 更新 HTML 星星
    html_files = get_html_files()
    print(f"🔍 扫描 {len(html_files)} 个 HTML 文件")
    
    updated = 0
    for f in html_files:
        changed, stars = update_html_stars(f, fav_map)
        if changed:
            updated += 1
            print(f"  ✏️ {f.name}: {stars} ★")
    
    print(f"✅ {updated}/{len(html_files)} 更新")
    
    # 生成季度精选
    print("📊 生成季度精选...")
    gen_script = REPO_DIR / "scripts" / "gen_quarterly.py"
    if gen_script.exists():
        result = subprocess.run(
            ["python3", str(gen_script)],
            capture_output=True, text=True, cwd=str(REPO_DIR)
        )
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")
    
    # 计算收藏总数统计（只在变更时打印）
    if updated > 0:
        print(f"\n📊 收藏统计：5月共 {len(starred)} 篇")
    else:
        print("\n📊 无变更")

if __name__ == "__main__":
    main()
