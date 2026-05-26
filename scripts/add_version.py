#!/usr/bin/env python3
"""Post-process all .html files to add ?v=TIMESTAMP to internal links.

This forces browsers to re-fetch pages when content changes.
Version = current timestamp, so every auto_sync cycle produces a new version.

Usage: python3 scripts/add_version.py
"""
import os, re
from datetime import datetime

BASE = "/mnt/d/LZ&AI/info-box"

def get_version():
    """Use current timestamp as version string."""
    return datetime.now().strftime("%Y%m%d%H%M")

def add_version_to_html(content, v):
    """Add ?v=HASH to all internal relative links in HTML."""
    # Strip script tags first — only modify hrefs in HTML content, not JS
    result = []
    in_script = False
    for line in content.split('\n'):
        if '<script' in line:
            in_script = True
        if in_script:
            result.append(line)
            if '</script>' in line:
                in_script = False
            continue

        def add_v(match):
            href = match.group(1)
            # Skip external, protocol-relative, anchors, mailto, javascript, tel
            if any(href.startswith(p) for p in ["http://", "https://", "//", "#", "mailto:", "javascript:", "tel:"]):
                return match.group(0)
            # Already has a version parameter?
            if "?v=" in href:
                # Replace existing version
                href = re.sub(r'\?v=[^"]*', f"?v={v}", href)
                return f'href="{href}"'
            # Add version
            sep = "&" if "?" in href else "?"
            return f'href="{href}{sep}v={v}"'

        result.append(re.sub(r'href="([^"]*)"', add_v, line))
    return '\n'.join(result)

def main():
    v = get_version()
    print(f"🔖 版本: {v}")

    count = 0
    for root, dirs, files in os.walk(BASE):
        # Skip .git directory and scripts
        dirs[:] = [d for d in dirs if d not in [".git", ".hermes", "__pycache__"]]
        for fname in files:
            if not fname.endswith(".html"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = add_version_to_html(content, v)
            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  ✓ {os.path.relpath(fpath, BASE)}")
                count += 1

    if count == 0:
        print("  没有需要更新的文件（版本未变）")
    else:
        print(f"\n✅ 已更新 {count} 个文件，版本 {v}")

if __name__ == "__main__":
    main()
