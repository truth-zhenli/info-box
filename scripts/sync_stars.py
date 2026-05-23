#!/usr/bin/env python3
"""
sync_stars.py — 将本地收藏星星刷入所有文献 HTML

读取 D:\LZ&AI\favorites.json（Resilio Sync 同步），将 ★/☆ 状态刷入
所有现有的文献 HTML 文件。

用法:
  python3 scripts/sync_stars.py
"""

import json
import os
import re

LOCAL_FAV_PATH = "/mnt/d/LZ&AI/碎片化信息盒/favorites.json"
REPO_BASE = "/mnt/d/LZ&AI/碎片化信息盒"
LITERATURE_DIR = os.path.join(REPO_BASE, "页面", "文献追踪")


def load_favs():
    """加载本地 favorites.json，返回完整数据 + lookup map。"""
    if not os.path.exists(LOCAL_FAV_PATH):
        print(f"⚠️ 本地 favorites.json 不存在: {LOCAL_FAV_PATH}")
        print(f"   从仓库复制一份作为初始版本。")
        return _copy_from_repo()

    with open(LOCAL_FAV_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    fav_map = {}
    for item in data:
        key = f"{item.get('title','')}|||{item.get('link','')}"
        fav_map[key] = item.get("starred", False)

    print(f"📖 读取本地 favorites.json: {len(data)} 条")
    return data, fav_map


def _copy_from_repo():
    """仓库版复制到本地（首次使用）。"""
    repo_fav = os.path.join(REPO_BASE, "favorites.json")
    if not os.path.exists(repo_fav):
        print("⚠️ 仓库也没有 favorites.json，跳过")
        return [], {}

    with open(repo_fav, "r", encoding="utf-8") as src:
        data = json.load(src)

    os.makedirs(os.path.dirname(LOCAL_FAV_PATH), exist_ok=True)
    with open(LOCAL_FAV_PATH, "w", encoding="utf-8") as dst:
        json.dump(data, dst, ensure_ascii=False, indent=2)

    print(f"📋 从仓库复制到本地: {len(data)} 条")
    fav_map = {}
    for item in data:
        key = f"{item.get('title','')}|||{item.get('link','')}"
        fav_map[key] = item.get("starred", False)
    return data, fav_map


def star_state(fav_map, title, link):
    key = f"{title}|||{link}"
    return "★" if fav_map.get(key) else "☆"


def sync_file(filepath, fav_map):
    """同步单个 HTML 文件的星星状态。返回是否修改。"""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    changes = 0

    # Match star-btn and update both textContent AND data-star attribute
    # Pattern: <span class="star-btn" ...>★</span> or ☆
    pattern = r'(<span class="star-btn"[^>]*?)>([★☆])(</span>)'

    def repl(m):
        nonlocal changes
        prefix = m.group(1)  # everything before >
        current = m.group(2)
        suffix = m.group(3)

        # Extract title and link from data attributes
        title_match = re.search(r'data-title="([^"]*?)"', prefix)
        link_match = re.search(r'data-link="([^"]*?)"', prefix)
        title = title_match.group(1) if title_match else ""
        link = link_match.group(1) if link_match else ""

        wanted = star_state(fav_map, title, link)
        if wanted != current:
            changes += 1

        # Always ensure data-star attribute is set
        if 'data-star="' in prefix:
            prefix = re.sub(r'data-star="[★☆]"', f'data-star="{wanted}"', prefix)
        else:
            prefix += f' data-star="{wanted}"'

        return f"{prefix}>{wanted}{suffix}"

    html = re.sub(pattern, repl, html)

    if html != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        name = os.path.basename(filepath)
        print(f"  ✏️ {name}: 更新 {changes} 个星星")
        return True
    return False


def main():
    print("=" * 40)
    print("⭐ Star Syncer")
    print("=" * 40)

    data, fav_map = load_favs()
    if not fav_map:
        print("⚠️ 无收藏数据，跳过")
        return

    # 扫描所有文献 HTML
    if not os.path.exists(LITERATURE_DIR):
        print(f"⚠️ 找不到文献目录: {LITERATURE_DIR}")
        return

    html_files = []
    for root, dirs, files in os.walk(LITERATURE_DIR):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    if not html_files:
        print("⚠️ 没有 HTML 文件")
        return

    print(f"🔍 扫描到 {len(html_files)} 个 HTML 文件")
    changed = 0
    for fp in sorted(html_files):
        if sync_file(fp, fav_map):
            changed += 1
    print(f"✅ {changed}/{len(html_files)} 个文件有更新")

    # 同步 favorites.json 到仓库
    repo_fav = os.path.join(REPO_BASE, "favorites.json")
    with open(repo_fav, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📋 favorites.json 已同步到仓库 ({len(data)} 条)")


if __name__ == "__main__":
    main()
