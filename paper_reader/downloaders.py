"""arXiv 下载器模块 - 处理论文搜索和下载"""

import os
import ssl
import certifi
import requests
from datetime import datetime, timedelta
import arxiv
import urllib3

from config import CONFIG

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ArxivDownloader:
    """arXiv论文下载器"""

    @staticmethod
    def _create_client():
        """创建带有正确SSL配置的arxiv客户端"""
        # 创建自定义SSL上下文
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        # 创建arxiv客户端，使用更长的超时时间
        return arxiv.Client(num_retries=3, delay_seconds=5, page_size=100)

    @staticmethod
    def search_papers(query, max_results=10, category=None, date_from=None):
        """搜索论文"""
        try:
            search_query = query
            if category:
                search_query = f"cat:{category} AND {query}"

            client = ArxivDownloader._create_client()
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )

            papers = []
            for result in client.results(search):
                paper = {
                    "arxiv_id": result.entry_id.split("/")[-1],
                    "title": result.title,
                    "authors": [str(a) for a in result.authors],
                    "abstract": result.summary,
                    "categories": result.categories,
                    "primary_category": result.primary_category,
                    "published": result.published.isoformat()
                    if result.published
                    else None,
                    "updated": result.updated.isoformat() if result.updated else None,
                    "pdf_url": result.pdf_url,
                }
                papers.append(paper)

            return papers
        except Exception as e:
            print(f"搜索论文失败: {e}")
            return []

    @staticmethod
    def get_paper_by_id(arxiv_id):
        """通过ID获取论文"""
        try:
            client = ArxivDownloader._create_client()
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(client.results(search))
            if results:
                result = results[0]
                return {
                    "arxiv_id": result.entry_id.split("/")[-1],
                    "title": result.title,
                    "authors": [str(a) for a in result.authors],
                    "abstract": result.summary,
                    "categories": result.categories,
                    "primary_category": result.primary_category,
                    "published": result.published.isoformat()
                    if result.published
                    else None,
                    "updated": result.updated.isoformat() if result.updated else None,
                    "pdf_url": result.pdf_url,
                }
            return None
        except Exception as e:
            print(f"获取论文失败: {e}")
            return None

    @staticmethod
    def download_pdf(arxiv_id, category=None):
        """下载PDF"""
        try:
            # 构建保存路径
            if category:
                save_dir = os.path.join(CONFIG["PDF_DIR"], category)
            else:
                save_dir = os.path.join(CONFIG["PDF_DIR"], "misc")
            os.makedirs(save_dir, exist_ok=True)

            filepath = os.path.join(save_dir, f"{arxiv_id}.pdf")

            # 检查是否已存在
            if os.path.exists(filepath):
                return True, filepath

            # 尝试使用arxiv库下载
            try:
                client = ArxivDownloader._create_client()
                search = arxiv.Search(id_list=[arxiv_id])
                results = list(client.results(search))

                if not results:
                    return False, "论文未找到"

                paper = results[0]
                paper.download_pdf(dirpath=save_dir, filename=f"{arxiv_id}.pdf")
                return True, filepath
            except Exception as arxiv_error:
                # 如果arxiv库失败，使用备用方法直接下载
                print(f"arxiv库下载失败: {arxiv_error}，尝试备用方法...")
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                # 使用requests下载，禁用SSL验证（仅用于开发环境）
                response = requests.get(
                    pdf_url,
                    verify=False,
                    timeout=60,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(response.content)

                return True, filepath

        except Exception as e:
            print(f"下载PDF失败: {e}")
            import traceback

            traceback.print_exc()
            return False, str(e)

    @staticmethod
    def get_latest_papers(categories=None, max_results=50):
        """获取最新论文"""
        try:
            today = datetime.now().date()
            # yesterday = today - timedelta(days=1)

            papers = []
            client = ArxivDownloader._create_client()

            search_categories = categories or ["cs.AI", "cs.CL", "cs.CV", "cs.LG"]

            for cat in search_categories[:5]:  # 限制分类数量
                search = arxiv.Search(
                    query=f"cat:{cat}",
                    max_results=max_results // len(search_categories),
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                )

                for result in client.results(search):
                    # 只获取最近2天的论文
                    if result.published:  # and result.published.date() >= yesterday:
                        paper = {
                            "arxiv_id": result.entry_id.split("/")[-1],
                            "title": result.title,
                            "authors": [str(a) for a in result.authors],
                            "abstract": result.summary,
                            "categories": result.categories,
                            "primary_category": result.primary_category,
                            "published": result.published.isoformat()
                            if result.published
                            else None,
                            "pdf_url": result.pdf_url,
                        }
                        papers.append(paper)

            return papers
        except Exception as e:
            print(f"获取最新论文失败: {e}")
            return []
