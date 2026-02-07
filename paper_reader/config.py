"""配置文件 - 集中管理所有配置参数"""

import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask 应用配置
CONFIG = {
    "READER_PORT": 8603,
    "STATS_PORT": 8605,
    "DB_PATH": os.path.join(BASE_DIR, "db", "reading_stats.db"),
    "PDF_DIR": os.path.join(BASE_DIR, "pdfs"),
    "LOG_DIR": os.path.join(BASE_DIR, "log"),
    "TEMPLATE_DIR": os.path.join(BASE_DIR, "templates"),
    "STATIC_DIR": os.path.join(BASE_DIR, "static"),
}

# arXiv 获取器配置
FETCHER_CONFIG = {
    "delay": 5,
    "download_pdf": True,
    "pdf_dir": CONFIG["PDF_DIR"],
}

# 词典数据库路径
DICT_DB_PATH = os.path.join(BASE_DIR, "ecdict.db")
