#!/usr/bin/env python3
"""Strip localStorage reading from quarterly page JS — v13 uses favorites.json only."""
from pathlib import Path
import re

REPO = Path("/mnt/d/LZ&AI/info-box")
FAV_DIR = REPO / "pages" / "papers" / "2026" / "fav"

for q in range(1, 5):
    path = FAV_DIR / f"q{q}.html"
    if not path.exists():
        continue
    content = path.read_text(encoding='utf-8')

    # Remove the entire <script> block and replace with minimal version
    # New script: just show what's pre-rendered, no localStorage reading
    new_script = """<script>
// 季度精选 — 纯预渲染版
// v13 系统下星星写入 favorites.json，不读 localStorage
</script>"""

    content = re.sub(
        r'<script>.*?</script>',
        new_script,
        content,
        count=1,
        flags=re.DOTALL
    )

    # Remove the footer about localStorage
    content = content.replace(
        '<div class="footer">预渲染版 · 点星星后刷新页面即可更新</div>',
        '<div class="footer">预渲染版 · 星星数据来自 favorites.json</div>'
    )

    path.write_text(encoding='utf-8')
    print(f"✓ {path.name}")

print("\nDone!")