"""
arXiv 论文阅读器包

主要模块：
- config: 配置管理
- constants: 常量定义
- utils: 工具函数
- database: 数据库管理
- downloaders: arXiv下载器
- translators: 翻译模块
- routes: API路由
- stats_service: 统计服务
"""

__version__ = "1.0.0"
__author__ = "paper_reader"

# 方便导入
from config import CONFIG
from database import db_manager
