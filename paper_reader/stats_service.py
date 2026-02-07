"""统计服务模块 - 后台任务和统计服务器"""

import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import CONFIG, FETCHER_CONFIG
from routes import app as main_app
from get_passage import ArxivRSSFetcher


def background_fetcher():
    """后台自动获取论文"""
    while True:
        try:
            print("🔄 后台获取论文...")
            fetcher = ArxivRSSFetcher(**FETCHER_CONFIG)
            categories = [
                "cs.AI",
                "cs.CC",
                "math.AG",
                "math.NT",
                "cs.ET",
                "cs.GL",
                "cs.IT",
            ]
            fetcher.run(categories)
            print("✓ 后台获取完成")
            time.sleep(6 * 3600)
        except Exception as e:
            print(f"✗ 后台获取错误: {e}")
            time.sleep(3600)


def run_stats_server():
    """在8605端口运行统计服务器"""
    stats_app = Flask(__name__)
    CORS(stats_app)

    @stats_app.route("/")
    def index():
        return main_app.view_functions["stats_page"]()

    @stats_app.route("/api/<path:path>", methods=["GET", "POST", "OPTIONS"])
    def api_proxy(path):
        try:
            with main_app.test_client() as client:
                query_string = request.query_string.decode("utf-8")
                if request.method == "POST":
                    resp = client.post(
                        f"/api/{path}",
                        data=request.get_data(),
                        content_type=request.content_type,
                        headers=dict(request.headers),
                    )
                elif request.method == "OPTIONS":
                    resp = client.open(
                        f"/api/{path}",
                        method="OPTIONS",
                        headers=dict(request.headers),
                    )
                else:
                    if query_string:
                        resp = client.get(
                            f"/api/{path}?{query_string}",
                            headers=dict(request.headers),
                        )
                    else:
                        resp = client.get(
                            f"/api/{path}",
                            headers=dict(request.headers),
                        )

                if resp.is_json:
                    return jsonify(resp.get_json()), resp.status_code
                else:
                    return resp.get_data(), resp.status_code, dict(resp.headers)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @stats_app.route("/api/stats/<path:path>", methods=["GET", "OPTIONS"])
    def stats_api_proxy(path):
        with main_app.test_client() as client:
            query_string = request.query_string.decode("utf-8")
            if query_string:
                resp = client.get(f"/api/stats/{path}?{query_string}")
            else:
                resp = client.get(f"/api/stats/{path}")
            return jsonify(resp.get_json())

    @stats_app.route("/api/daily", methods=["GET", "OPTIONS"])
    def daily_proxy():
        with main_app.test_client() as client:
            query_string = request.query_string.decode("utf-8")
            if query_string:
                resp = client.get(f"/api/daily?{query_string}")
            else:
                resp = client.get("/api/daily")
            return jsonify(resp.get_json())

    print(f"📊 统计服务器启动: http://localhost:{CONFIG['STATS_PORT']}")
    stats_app.run(host="0.0.0.0", port=CONFIG["STATS_PORT"], threaded=True, debug=False)


def start_background_services(enable_fetch=False):
    """启动后台服务"""
    # 应用启动时更新每日统计数据
    from database import db_manager

    try:
        db_manager.update_daily_stats()
        print("✓ 统计数据已初始化")
    except Exception as e:
        print(f"⚠ 统计数据初始化失败: {e}")

    # 启动后台获取线程（如果启用）
    if enable_fetch:
        fetcher_thread = threading.Thread(target=background_fetcher, daemon=True)
        fetcher_thread.start()
        print("🔄 后台论文获取已启用")
    else:
        print("ℹ️ 后台论文获取已禁用（使用 --fetch 参数启用）")

    # 启动统计服务器（在另一个线程）
    stats_thread = threading.Thread(target=run_stats_server, daemon=True)
    stats_thread.start()


def start_main_server():
    """启动主服务器"""
    print(f"📖 阅读器启动: http://localhost:{CONFIG['READER_PORT']}")
    from routes import app

    app.run(host="0.0.0.0", port=CONFIG["READER_PORT"], threaded=True, debug=True)
