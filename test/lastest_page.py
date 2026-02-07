


# ==================== arXiv 下载工具 ====================
import ssl
import certifi
import arxiv
import os
from datetime import datetime, timedelta

class ArxivDownloader:
    """arXiv论文下载器"""

    @staticmethod
    def _create_client():
        """创建带有正确SSL配置的arxiv客户端"""
        # 创建自定义SSL上下文
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        # 创建arxiv客户端，使用更长的超时时间
        return arxiv.Client(
            num_retries=3,
            delay_seconds=5,
            page_size=100
        )

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
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            papers = []
            for result in client.results(search):
                paper = {
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'authors': [str(a) for a in result.authors],
                    'abstract': result.summary,
                    'categories': result.categories,
                    'primary_category': result.primary_category,
                    'published': result.published.isoformat() if result.published else None,
                    'updated': result.updated.isoformat() if result.updated else None,
                    'pdf_url': result.pdf_url
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
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'authors': [str(a) for a in result.authors],
                    'abstract': result.summary,
                    'categories': result.categories,
                    'primary_category': result.primary_category,
                    'published': result.published.isoformat() if result.published else None,
                    'updated': result.updated.isoformat() if result.updated else None,
                    'pdf_url': result.pdf_url
                }
            return None
        except Exception as e:
            print(f"获取论文失败: {e}")
            return None


    @staticmethod
    def get_latest_papers(categories=None, max_results=10):
        """获取最新论文"""
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            papers = []
            client = ArxivDownloader._create_client()

            search_categories = categories or ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG']

            for cat in search_categories[:5]:  # 限制分类数量
                search = arxiv.Search(
                    query=f"cat:{cat}",
                    max_results=max_results // len(search_categories),
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )

                for result in client.results(search):
                    # 只获取最近2天的论文
                    if result.published:  # and result.published.date() >= yesterday:
                        paper = {
                            'arxiv_id': result.entry_id.split('/')[-1],
                            'title': result.title,
                            'authors': [str(a) for a in result.authors],
                            'abstract': result.summary,
                            'categories': result.categories,
                            'primary_category': result.primary_category,
                            'published': result.published.isoformat() if result.published else None,
                            'pdf_url': result.pdf_url
                        }
                        papers.append(paper)

            return papers
        except Exception as e:
            print(f"获取最新论文失败: {e}")
            return []

arxiv_downloader = ArxivDownloader()
print(arxiv_downloader.get_latest_papers())
