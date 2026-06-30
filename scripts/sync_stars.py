#!/usr/bin/env python3
"""
⭐ Star Syncer v2 — 以 favorites.json 为唯一真理源

v13 星星系统：取消即删除，favorites.json 只保留当前星标的条目。
所以不再需要与 git HEAD 合并——直接读取 disk 上的 favorites.json。

流程：
1. 读取 Resilio Sync 同步来的 favorites.json
2. 更新所有 HTML 每日页面的星星状态
3. gen_quarterly.py 负责生成季度精选和更新 papers.html 计数
"""
import json
import subprocess
import sys
import re
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
FAV_JSON = REPO_DIR / "favorites.json"
PAPERS_DIR = REPO_DIR / "pages" / "papers"


def get_favs():
    """读取 favorites.json（Resilio Sync 同步来的就是真理）"""
    if not FAV_JSON.exists():
        return []
    with open(FAV_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def get_html_files():
    """扫描所有日期 HTML 文件"""
    files = []
    for f in sorted(PAPERS_DIR.rglob("????/??/????-??-??.html")):
        if f.suffix == ".html":
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
        old_d = block2[last_gt + 1:]
        if old_d in ("★", "☆"):
            content = content[:star_start + last_gt + 1] + new_char + content[star_start + last_gt + 2:]

    if content != orig:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, len(re.findall(r'data-star="★"', content))
    return False, len(re.findall(r'data-star="★"', content))


def main():
    print("=" * 40)
    print("⭐ Star Syncer v2")
    print("=" * 40)

    favs = get_favs()
    print(f"📖 favorites.json: {len(favs)} 条")

    starred = [i for i in favs if i.get("starred")]
    print(f"⭐ 星标: {len(starred)} 篇")
    for s in starred:
        print(f"  ✅ {s.get('date', '?')} | {s.get('title', '?')[:55]}")

    # 构建收藏 map：link → starred
    fav_map = {item["link"]: item.get("starred", False) for item in favs}

    # 更新 HTML 星星
    html_files = get_html_files()
    print(f"🔍 扫描 {len(html_files)} 个 HTML 文件")

    updated = 0
    total_stars = 0
    for f in html_files:
        changed, stars = update_html_stars(f, fav_map)
        if changed:
            updated += 1
            print(f"  ✏️ {f.name}: {stars} ★")
        total_stars += stars

    print(f"✅ {updated}/{len(html_files)} 更新，共 {total_stars} ★")

    # 生成季度精选（由 gen_quarterly.py 负责）
    print("📊 生成季度精选...")
    gen_script = REPO_DIR / "scripts" / "gen_quarterly.py"
    if gen_script.exists():
        result = subprocess.run(
            ["python3", str(gen_script)],
            capture_output=True, text=True, cwd=str(REPO_DIR)
        )
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")

    if updated > 0:
        print(f"\n📊 收藏统计：共 {len(starred)} 篇")


if __name__ == "__main__":
    main()
