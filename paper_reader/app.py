#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
arXiv 论文阅读器 - 主应用入口

这是一个用于阅读 arXiv 论文并学习英文的应用程序。
主要功能包括：
- 论文搜索和下载
- PDF 阅读
- 单词翻译
- 学习统计
"""

import sys
import ssl
import certifi
import urllib3

# 修复Windows SSL证书验证问题
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context

# 导入路由和后台服务
from routes import app
from stats_service import start_background_services, start_main_server


if __name__ == "__main__":
    # 检查是否禁用后台下载
    enable_background_fetch = "--fetch" in sys.argv

    # 启动后台服务
    start_background_services(enable_fetch=enable_background_fetch)

    # 启动主服务器
    start_main_server()
