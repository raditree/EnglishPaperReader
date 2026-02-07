"""API 路由模块 - 处理所有 HTTP 路由"""

import os
import time
import sqlite3
import shutil
import re
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

from config import CONFIG
from constants import ARXIV_CATEGORIES
from utils import error_handler
from database import db_manager
from downloaders import ArxivDownloader
from translators import call_translator, get_global_batch_translator

# 创建 Flask 应用
app = Flask(
    __name__, template_folder=CONFIG["TEMPLATE_DIR"], static_folder=CONFIG["STATIC_DIR"]
)
CORS(app)


# ==================== 页面路由 ====================
@app.route("/")
def reader_page():
    """阅读器主页面"""
    return render_template("reader.html")


@app.route("/stats")
def stats_page():
    """统计数据页面"""
    return render_template("stats.html")


# ==================== 论文相关路由 ====================
@app.route("/api/papers")
def get_papers():
    """获取本地可用论文列表"""
    papers = []
    pdf_dir = CONFIG["PDF_DIR"]

    if os.path.exists(pdf_dir):
        for category in os.listdir(pdf_dir):
            cat_path = os.path.join(pdf_dir, category)
            if os.path.isdir(cat_path):
                for pdf in os.listdir(cat_path):
                    if pdf.endswith(".pdf"):
                        arxiv_id = pdf.replace(".pdf", "")
                        paper_info = db_manager.get_paper_by_id(arxiv_id)
                        papers.append(
                            {
                                "id": arxiv_id,
                                "category": category,
                                "filename": pdf,
                                "path": f"{category}/{pdf}",
                                "is_read": paper_info["is_read"] if paper_info else 0,
                                "read_count": paper_info["read_count"]
                                if paper_info
                                else 0,
                                "title": paper_info["title"]
                                if paper_info and paper_info["title"]
                                else arxiv_id,
                            }
                        )

    return jsonify(papers)


@app.route("/api/papers/search", methods=["POST"])
@error_handler
def search_papers():
    """搜索论文"""
    data = request.json or {}
    query = data.get("query", "")
    category = data.get("category")
    max_results = data.get("max_results", 10)

    if not query:
        return jsonify({"error": "搜索关键词不能为空"}), 400

    papers = ArxivDownloader.search_papers(query, max_results, category)

    # 检查本地是否已下载
    for paper in papers:
        local_info = db_manager.get_paper_by_id(paper["arxiv_id"])
        if local_info:
            paper["is_downloaded"] = local_info["local_path"] is not None
            paper["is_read"] = local_info["is_read"]
            paper["local_path"] = local_info["local_path"]
        else:
            paper["is_downloaded"] = False
            paper["is_read"] = False

    return jsonify({"papers": papers})


@app.route("/api/papers/latest")
@error_handler
def get_latest_papers_api():
    """获取最新论文"""
    categories = (
        request.args.get("categories", "").split(",")
        if request.args.get("categories")
        else None
    )
    max_results = request.args.get("max_results", 20, type=int)

    papers = ArxivDownloader.get_latest_papers(categories, max_results)

    # 检查本地状态
    for paper in papers:
        local_info = db_manager.get_paper_by_id(paper["arxiv_id"])
        if local_info:
            paper["is_downloaded"] = local_info["local_path"] is not None
            paper["is_read"] = local_info["is_read"]
        else:
            paper["is_downloaded"] = False
            paper["is_read"] = False

    return jsonify({"papers": papers})


@app.route("/api/papers/download", methods=["POST", "OPTIONS"])
@error_handler
def download_paper():
    """下载论文"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json or {}
    arxiv_id = data.get("arxiv_id")
    category = data.get("category")

    if not arxiv_id:
        return jsonify({"error": "arxiv_id不能为空"}), 400

    try:
        # 先获取论文信息
        paper_info = ArxivDownloader.get_paper_by_id(arxiv_id)
        if not paper_info:
            return jsonify({"error": "论文未找到"}), 404

        # 确定分类
        if not category:
            category = paper_info.get("primary_category", "misc").replace(".", "_")

        # 下载PDF
        success, result = ArxivDownloader.download_pdf(arxiv_id, category)

        if success:
            # 记录到数据库
            local_path = f"{category}/{arxiv_id}.pdf"
            db_manager.record_paper(
                arxiv_id=arxiv_id,
                title=paper_info["title"],
                authors=paper_info["authors"],
                abstract=paper_info["abstract"],
                categories=paper_info["categories"],
                primary_category=paper_info["primary_category"],
                published_date=paper_info["published"],
                pdf_url=paper_info["pdf_url"],
                local_path=local_path,
            )
            return jsonify(
                {
                    "success": True,
                    "arxiv_id": arxiv_id,
                    "path": local_path,
                    "title": paper_info["title"],
                }
            )
        else:
            return jsonify({"error": result}), 500
    except Exception as e:
        print(f"下载论文失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"下载失败: {str(e)}"}), 500


@app.route("/api/papers/<arxiv_id>")
@error_handler
def get_paper_detail(arxiv_id):
    """获取论文详情"""
    # 先查本地
    paper = db_manager.get_paper_by_id(arxiv_id)

    if not paper:
        # 从arXiv获取
        paper_info = ArxivDownloader.get_paper_by_id(arxiv_id)
        if paper_info:
            return jsonify(paper_info)
        return jsonify({"error": "论文未找到"}), 404

    return jsonify(paper)


@app.route("/api/categories")
@error_handler
def get_categories():
    """获取所有可用的arXiv分类"""
    return jsonify(ARXIV_CATEGORIES)


@app.route("/api/paper/<path:filename>")
def serve_pdf(filename):
    """提供PDF文件"""
    try:
        safe_path = (
            os.path.join(CONFIG["PDF_DIR"], filename)
            .replace("../", "")
            .replace("..\\", "")
        )
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"文件不存在: {filename}")
        return send_from_directory(CONFIG["PDF_DIR"], filename)
    except Exception as e:
        print(f"PDF服务错误: {e}")
        return jsonify({"error": str(e)}), 404


# ==================== 翻译相关路由 ====================
@app.route("/api/translate", methods=["POST", "OPTIONS"])
@error_handler
def translate_word():
    """翻译单词接口"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    word = data.get("word", "")
    context = data.get("context", "")

    if not word or not isinstance(word, str):
        return jsonify({"error": "Invalid word parameter"}), 400

    translation = call_translator(word, context)

    session_id = data.get("session_id", "default")
    paper_id = data.get("paper_id", "")
    category = data.get("category", "")

    db_manager.record_word_query(
        word=word,
        context=context,
        translation=translation,
        paper_id=paper_id,
        category=category,
        session_id=session_id,
    )

    if isinstance(translation, str) and translation.startswith("[翻译错误]"):
        return jsonify(
            {
                "word": word,
                "translation": translation,
                "context": context,
                "error": "翻译服务出现错误",
            }
        ), 500

    return jsonify({"word": word, "translation": translation, "context": context})


@app.route("/api/translate/batch", methods=["POST", "OPTIONS"])
@error_handler
def batch_translate():
    """批量翻译接口 - 用于预加载论文单词"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    words = data.get("words", [])
    if not words or not isinstance(words, list):
        return jsonify({"error": "Invalid words parameter, expected a list"}), 400

    # 过滤和清理单词
    clean_words = []
    for w in words:
        if isinstance(w, str):
            clean_word = w.lower().strip()
            if clean_word and len(clean_word) >= 2:
                clean_words.append(clean_word)

    # 去重
    clean_words = list(set(clean_words))

    translator = get_global_batch_translator()

    # 批量翻译
    results = translator.batch_translate(clean_words)

    # 转换为JSON格式
    response_data = {}
    for word, result in results.items():
        response_data[word] = {
            "translation": result.translation,
            "phonetic": result.phonetic,
            "meaning": result.meaning,
            "is_cached": result.is_cached,
            "query_time_ms": round(result.query_time_ms, 2),
        }

    return jsonify(
        {
            "words": response_data,
            "total": len(clean_words),
            "cached": sum(1 for r in results.values() if r.is_cached),
        }
    )


@app.route("/api/translate/preload", methods=["POST", "OPTIONS"])
@error_handler
def preload_paper_translations():
    """
    预加载论文翻译 - 从PDF文本中提取并翻译所有单词
    接收PDF文本内容，返回所有单词的翻译
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    text_content = data.get("text", "")
    paper_id = data.get("paper_id", "")

    if not text_content:
        return jsonify({"error": "No text content provided"}), 400

    translator = get_global_batch_translator()

    # 提取单词
    start_time = time.time()
    words = translator.extract_words_from_text(text_content)
    extract_time = (time.time() - start_time) * 1000

    # 批量翻译
    results = translator.batch_translate(words)

    # 转换为JSON格式
    translations = {}
    for word, result in results.items():
        translations[word] = {
            "translation": result.translation,
            "phonetic": result.phonetic,
            "meaning": result.meaning,
            "is_cached": result.is_cached,
        }

    return jsonify(
        {
            "paper_id": paper_id,
            "total_words": len(words),
            "extract_time_ms": round(extract_time, 2),
            "translations": translations,
        }
    )


@app.route("/api/translate/cache/stats")
@error_handler
def get_translation_cache_stats():
    """获取翻译缓存统计信息"""
    translator = get_global_batch_translator()
    stats = translator.get_cache_stats()
    return jsonify(stats)


@app.route("/api/translate/cache/clear", methods=["POST"])
@error_handler
def clear_translation_cache():
    """清空翻译缓存"""
    translator = get_global_batch_translator()
    translator.clear_cache()
    return jsonify({"success": True, "message": "Cache cleared"})


# ==================== 统计相关路由 ====================
@app.route("/api/stats/<query_type>")
@error_handler
def query_statistics(query_type):
    """统计查询接口"""
    params = request.args.to_dict()
    for key in ["days", "limit"]:
        if key in params:
            params[key] = int(params[key])
    result = db_manager.query_stats(query_type, **params)
    return jsonify(result)


@app.route("/api/daily")
@error_handler
def get_daily_stats():
    """获取每日统计数据"""
    days = request.args.get("days", 30, type=int)
    conn = sqlite3.connect(CONFIG["DB_PATH"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM daily_stats
        WHERE date >= DATE('now', '-{} days')
        ORDER BY date ASC
    """.format(days)
    )

    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(stats)


# ==================== 会话管理路由 ====================
@app.route("/api/session/start", methods=["POST", "OPTIONS"])
@error_handler
def start_session():
    """开始阅读会话"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    session_id = data.get("session_id", str(int(time.time())))
    paper_id = data.get("paper_id", "")
    category = data.get("category", "")

    db_manager.start_session(session_id, paper_id, category)
    return jsonify({"session_id": session_id, "status": "started"})


@app.route("/api/session/end", methods=["POST", "OPTIONS"])
@error_handler
def end_session():
    """结束阅读会话"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    session_id = data.get("session_id", "")
    duration = data.get("duration_seconds", 0)
    pages_read = data.get("pages_read", 0)

    db_manager.end_session(session_id, duration, pages_read)
    return jsonify({"status": "ended", "session_id": session_id})


# ==================== 用户数据管理路由 ====================
@app.route("/api/user/reset", methods=["POST"])
@error_handler
def reset_user_data():
    """重置用户数据"""
    data = request.json or {}
    reset_type = data.get("type", "soft")  # soft: 只重置阅读记录, hard: 删除所有包括PDF

    # 重置数据库（hard_reset=True时同时删除papers表数据）
    db_manager.reset_all_data(hard_reset=(reset_type == "hard"))

    if reset_type == "hard":
        # 删除所有PDF文件
        pdf_dir = CONFIG["PDF_DIR"]
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
            os.makedirs(pdf_dir)

    return jsonify(
        {
            "success": True,
            "message": "用户数据已重置"
            + ("（包含PDF）" if reset_type == "hard" else ""),
        }
    )


@app.route("/api/user/import-familiar", methods=["POST"])
@error_handler
def import_familiar_words():
    """导入熟词"""
    data = request.json or {}
    text = data.get("text", "")
    source = data.get("source", "import")

    if not text:
        return jsonify({"error": "文本内容不能为空"}), 400

    # 提取英文单词
    words = re.findall(r"[a-zA-Z]{2,}", text)
    words = list(set(w.lower() for w in words))  # 去重

    # 添加到熟词表
    added, batch_id = db_manager.add_familiar_words(words, source)

    # 更新每日统计数据
    db_manager.update_daily_stats()

    return jsonify(
        {
            "success": True,
            "added": added,
            "total_extracted": len(words),
            "batch_id": batch_id,
        }
    )


@app.route("/api/user/familiar-words")
@error_handler
def get_familiar_words():
    """获取熟词列表"""
    words = db_manager.get_familiar_words()
    return jsonify({"words": words, "count": len(words)})


@app.route("/api/user/familiar-words/details")
@error_handler
def get_familiar_words_details():
    """获取熟词详细列表（支持分页和搜索）"""
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    search = request.args.get("search", "", type=str)
    result = db_manager.get_familiar_words_with_details(limit, offset, search)
    return jsonify(result)


@app.route("/api/user/import-batches")
@error_handler
def get_import_batches():
    """获取导入批次列表"""
    batches = db_manager.get_import_batches()
    return jsonify({"batches": batches})


@app.route("/api/user/undo-import/<batch_id>", methods=["POST"])
@error_handler
def undo_import_batch(batch_id):
    """撤销指定批次的导入"""
    deleted = db_manager.undo_import_batch(batch_id)
    # 更新统计数据
    db_manager.update_daily_stats()
    return jsonify({"success": True, "deleted": deleted})
