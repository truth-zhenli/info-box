#!/usr/bin/env python3
"""
fav_server.py — 本地星星收藏服务
运行在 D:\LZ&AI\ 目录下，接收 localhost:7898 的收藏请求，写 favorites.json

启动方式：
  cd D:\LZ&AI\
  python fav_server.py

或者用 Windows 任务计划程序开机自启。
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# 确定 favorites.json 路径（与脚本同目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
FAV_PATH = os.path.join(BASE_DIR, "favorites.json")

# 跨域头
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

def load_favs():
    """加载 favorites.json，不存在则返回空列表"""
    if not os.path.exists(FAV_PATH):
        return []
    with open(FAV_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_favs(data):
    """写回 favorites.json"""
    with open(FAV_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def toggle_star(paper_data):
    """
    切换收藏状态。
    paper_data: { title, link, cnTitle, journal, authors, date }
    返回: { status: "starred"|"unstarred" }
    """
    favs = load_favs()
    title = paper_data.get("title", "")
    link = paper_data.get("link", "")

    # 查找已有记录
    for item in favs:
        if item.get("title") == title and item.get("link") == link:
            # 切换状态
            new_state = not item.get("starred", False)
            item["starred"] = new_state
            # 更新元数据
            for key in ("cnTitle", "journal", "authors", "date"):
                if key in paper_data:
                    item[key] = paper_data[key]
            save_favs(favs)
            return {"status": "starred" if new_state else "unstarred", "index": favs.index(item)}

    # 新增条目（默认为收藏）
    paper_data["starred"] = True
    favs.append(paper_data)
    save_favs(favs)
    return {"status": "starred", "index": len(favs) - 1}

class FavHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/fav" or parsed.path == "/favorites.json":
            # 返回完整 favorites.json
            favs = load_favs()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            for k, v in CORS_HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(json.dumps(favs, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/fav":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            try:
                paper_data = json.loads(body.decode("utf-8"))
                result = toggle_star(paper_data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                for k, v in CORS_HEADERS.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')

    def log_message(self, format, *args):
        """简化控制台输出"""
        print(f"[fav_server] {args[0]} {args[1]}", flush=True)

def main():
    port = 7898
    # 如果传了端口参数就用它
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server = HTTPServer(("127.0.0.1", port), FavHandler)
    print(f"⭐ fav_server running on http://127.0.0.1:{port}")
    print(f"📁 favorites.json at: {FAV_PATH}")
    print("⏎ CTRL+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped")
        server.server_close()

if __name__ == "__main__":
    main()
