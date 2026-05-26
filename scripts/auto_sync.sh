#!/bin/bash
# 自动同步星星 → HTML → 季度精选 → git push
# 由 cronjob 每15分钟调用一次（no_agent模式）
# 设计：只读 favorites.json，不修改（避免 Resilio Sync 冲突）

REPO_DIR="/mnt/d/LZ&AI/info-box"
LOG="$REPO_DIR/.auto_sync_log"
LAST_HASH="$REPO_DIR/.last_fav_hash"

cd "$REPO_DIR" || exit 1

# 检查 favorites.json 是否存在
[ -f favorites.json ] || exit 0

# 计算当前 MD5（只读，不修改文件）
CUR_HASH=$(md5sum favorites.json | cut -d' ' -f1)

# 读取上次 hash
[ -f "$LAST_HASH" ] && LAST=$(cat "$LAST_HASH") || LAST=""

# 没变化就跳过
[ "$CUR_HASH" = "$LAST" ] && exit 0

# 运行 sync_stars.py、gen_quarterly.py、add_version.py（缓存刷新）
python3 scripts/sync_stars.py 2>&1 | tail -10
python3 scripts/gen_quarterly.py 2>&1 | tail -10
python3 scripts/add_version.py 2>&1 | tail -10

# 检查 git 是否有变更
if git diff --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M') 无变更" >> "$LOG"
    echo "$CUR_HASH" > "$LAST_HASH"
    exit 0
fi

# 有变更，提交并推送
git add -A
git commit -m "🔄 自动同步星星 $(date '+%m-%d %H:%M')" 2>&1 | tail -1 >> "$LOG"

# 通过代理推送（VPN 需要）
export http_proxy="http://127.0.0.1:7897"
export https_proxy="http://127.0.0.1:7897"
git config http.version HTTP/1.1 2>/dev/null

if git push origin main 2>&1 | tail -3 >> "$LOG"; then
    echo "$(date '+%Y-%m-%d %H:%M') ✅ 已推送" >> "$LOG"
else
    # 重试不带代理（有时校园网直连更快）
    unset http_proxy https_proxy
    git push origin main 2>&1 | tail -3 >> "$LOG"
fi

echo "$CUR_HASH" > "$LAST_HASH"
