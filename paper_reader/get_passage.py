import requests
import requests.exceptions
import xml.etree.ElementTree as ET
import time
import re
import os
import ssl
import certifi
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlparse

# 修复Windows SSL证书验证问题
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context


class ArxivRSSFetcher:
    def __init__(self, delay=5, download_pdf=True, pdf_dir="pdfs"):
        self.delay = delay
        self.download_pdf = download_pdf
        self.pdf_dir = pdf_dir
        self.base_url = "https://rss.arxiv.org/rss/"

        # 创建PDF下载目录
        if self.download_pdf and not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
            print(f"✓ 创建PDF目录: {self.pdf_dir}")

    def fetch_rss_feed(self, category):
        """获取指定分类的RSS feed"""
        print(f"\n正在获取 RSS: {category}...")
        url = f"{self.base_url}{category}"

        try:
            max_retries = 3
            base_delay = 1
            success = False
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get(
                        url,
                        timeout=(10, 30),  # 10s连接超时,30s读取超时
                        headers={
                            'User-Agent': 'ArxivRSSFetcher/1.0 (research purpose)',
                            'Accept': 'application/rss+xml, application/xml, text/xml'
                        }
                    )
                    response.raise_for_status()
                    success = True
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                    if attempt == max_retries:
                        print(f"  Attempt {attempt+1}/{max_retries+1} failed: {str(e)}, 无更多重试")
                        raise
                    delay = base_delay * (2 ** attempt)
                    print(f"  Attempt {attempt+1}/{max_retries+1} failed: {str(e)}, {delay}s后重试...")
                    time.sleep(delay)
            if not success:
                return []

            papers = self.parse_rss(response.content, category)
            print(f"  ✓ RSS解析完成，获取 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            print(f"  ✗ 获取失败: {e}")
            return []

    def parse_rss(self, xml_content, source_category):
        """解析RSS XML"""
        root = ET.fromstring(xml_content)
        ns = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'atom': 'http://www.w3.org/2005/Atom'
        }

        papers = []
        channel = root.find('channel')

        if channel is None:
            return papers

        feed_title = channel.findtext('title', 'Unknown Feed')
        feed_date = channel.findtext('lastBuildDate', '')

        print(f"  Feed标题: {feed_title}")
        print(f"  更新时间: {feed_date}")

        for item in channel.findall('item'):
            paper = {}

            # 基本字段
            paper['title'] = self._clean_text(item.findtext('title', ''))
            paper['link'] = item.findtext('link', '')

            # 提取arXiv ID
            arxiv_id = paper['link'].split('/')[-1] if paper['link'] else ''
            paper['arxiv_id'] = arxiv_id

            # 构建PDF链接
            paper['pdf_url'] = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ''

            # 作者
            author_text = item.findtext('dc:creator', '', ns)
            if author_text:
                authors = [a.strip() for a in re.split(r',|\band\b', author_text) if a.strip()]
                paper['authors'] = authors
            else:
                paper['authors'] = []

            # 日期
            paper['pub_date'] = item.findtext('pubDate', '')
            paper['dc_date'] = item.findtext('dc:date', '', ns)

            # 分类
            categories = []
            for cat in item.findall('category'):
                if cat.text:
                    categories.append(cat.text)
            paper['categories'] = categories if categories else [source_category]
            paper['source_category'] = source_category

            # 摘要
            description = item.findtext('description', '')
            paper['abstract'] = self._extract_abstract(description)

            papers.append(paper)

        return papers

    def _extract_abstract(self, html_text):
        """从HTML中提取纯文本摘要"""
        if not html_text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', html_text)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if 'Abstract:' in text:
            text = text.split('Abstract:', 1)[1].strip()
        return text

    def _clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def download_pdf_file(self, paper, category_dir=None):
        """
        下载PDF文件
        返回: (成功/失败, 文件路径/错误信息, 文件大小)
        """
        if not paper.get('pdf_url'):
            return False, "无PDF链接", 0

        arxiv_id = paper['arxiv_id']
        pdf_url = paper['pdf_url']

        # 构建保存路径
        if category_dir:
            save_dir = os.path.join(self.pdf_dir, self._sanitize_filename(category_dir))
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
        else:
            save_dir = self.pdf_dir

        # 文件名: arxiv_id.pdf
        filename = f"{arxiv_id}.pdf"
        filepath = os.path.join(save_dir, filename)

        # 检查是否已存在
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"    ⏭️  PDF已存在: {filename} ({self._format_size(file_size)})")
            return True, filepath, file_size

        try:
            print(f"    ⬇️  正在下载 PDF: {arxiv_id}...")

            max_retries =3
            base_delay=1
            for attempt in range(max_retries+1):
                try:
                    response = requests.get(
                        pdf_url,
                        timeout=(10,30),  # 10s连接超时,30s读取超时
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        },
                        stream=True  # 流式下载大文件
                    )
                    response.raise_for_status()
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                    if attempt == max_retries:
                        print(f"    Attempt {attempt+1}/{max_retries+1} failed: {str(e)}, 无更多重试")
                        raise
                    delay = base_delay*(2**attempt)
                    print(f"    Attempt {attempt+1}/{max_retries+1} failed: {str(e)}, {delay}s后重试...")
                    time.sleep(delay)

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))

            # 保存文件
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            # 验证文件
            if os.path.exists(filepath):
                actual_size = os.path.getsize(filepath)
                print(f"    ✓ 下载完成: {filename} ({self._format_size(actual_size)})")
                return True, filepath, actual_size
            else:
                return False, "文件保存失败", 0

        except Exception as e:
            print(f"    ✗ 下载失败: {e}")
            # 清理不完整文件
            if os.path.exists(filepath):
                os.remove(filepath)
            return False, str(e), 0

    def _sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def generate_markdown(self, papers_by_category, download_results):
        """生成Markdown报告"""
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        fetch_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        md_content = f"""# arXiv 每日论文精选 (RSS + PDF) - {today_str}

> 数据获取时间: {fetch_time}  
> 数据源: arXiv RSS Feed  
> 功能: RSS获取 + 自动PDF下载

## 概览

| 分类 | 论文标题 | 作者数 | PDF状态 | 文件大小 |
|------|----------|--------|---------|----------|
"""

        for cat, papers in papers_by_category.items():
            if papers:
                p = papers[0]
                author_count = len(p['authors'])
                title = p['title'][:35] + '...' if len(p['title']) > 35 else p['title']

                # PDF状态
                success, path, size = download_results.get(cat, (False, "未下载", 0))
                if success:
                    pdf_status = "✓ 已下载"
                    size_str = self._format_size(size)
                else:
                    pdf_status = "✗ 失败"
                    size_str = "-"
            else:
                title = "无新论文"
                author_count = 0
                pdf_status = "-"
                size_str = "-"

            md_content += f"| `{cat}` | {title} | {author_count} | {pdf_status} | {size_str} |\n"

        md_content += "\n---\n\n"

        # 详细内容
        for cat, papers in papers_by_category.items():
            md_content += f"## {cat}\n\n"

            if not papers:
                md_content += "> ⚠️ 该分类今日暂无新提交的论文\n\n"
                md_content += "---\n\n"
                continue

            paper = papers[0]

            # 标题
            md_content += f"### {paper['title']}\n\n"

            # 元信息
            md_content += "**作者:** "
            if len(paper['authors']) <= 3:
                md_content += ", ".join(paper['authors']) if paper['authors'] else "未知"
            else:
                md_content += ", ".join(paper['authors'][:3]) + f" 等 **{len(paper['authors'])}** 位"
            md_content += "\n\n"

            md_content += f"**arXiv ID:** [{paper['arxiv_id']}]({paper['link']})\n\n"
            md_content += f"**发布日期:** {paper['pub_date']}\n\n"

            # PDF下载信息
            success, path, size = download_results.get(cat, (False, "未下载", 0))
            if success:
                md_content += f"**PDF文件:** `{path}` ({self._format_size(size)})\n\n"
                md_content += f"**PDF链接:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n"
            else:
                md_content += f"**PDF链接:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n"
                if not success and path != "未下载":
                    md_content += f"**下载状态:** ❌ {path}\n\n"

            # 分类
            if paper['categories']:
                md_content += "**分类:** " + ", ".join([f"`{c}`" for c in paper['categories']]) + "\n\n"

            # 摘要
            md_content += "#### 摘要\n\n"
            if paper['abstract']:
                md_content += f"{paper['abstract']}\n\n"
            else:
                md_content += "> 摘要未提供\n\n"

            md_content += "---\n\n"

        # 技术信息
        total_papers = sum(1 for p in papers_by_category.values() if p)
        success_downloads = sum(1 for s, _, _ in download_results.values() if s)

        md_content += f"""
## 下载统计

- **总分类数**: {len(papers_by_category)}
- **成功获取RSS**: {total_papers}/{len(papers_by_category)}
- **PDF下载成功**: {success_downloads}/{total_papers}
- **PDF存储目录**: `{self.pdf_dir}/`

## 技术信息

- **获取方式**: Standard RSS 2.0 Feed
- **RSS URL**: `https://rss.arxiv.org/rss/<category>`
- **请求间隔**: {self.delay} 秒
- **PDF下载**: 自动下载到 `{self.pdf_dir}/<category>/` 目录

### 文件命名规则

PDF文件以arXiv ID命名，格式为: `<arxiv_id>.pdf`  
例如: `2501.12345.pdf`

---

*本文件由 ArxivRSSFetcher 自动生成*  
*数据来源于 arXiv.org*
"""

        return md_content

    # 修复 3: 修改 save_markdown 方法中的路径（get_passage.py 中）

    def save_markdown(self, content, filename=None):
        """保存Markdown文件"""
        if filename is None:
            date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
            # 使用绝对路径或确保目录存在
            log_dir = os.path.join(os.path.dirname(__file__), 'log')
            os.makedirs(log_dir, exist_ok=True)
            filename = os.path.join(log_dir, f"arxiv_daily_rss_{date_str}.md")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✓ Markdown报告已保存: {filename}")
        return filename

    def run(self, categories):
        """主运行函数"""
        print("=" * 70)
        print("arXiv RSS + PDF 自动下载器")
        print(f"目标分类: {len(categories)} 个")
        print(f"请求间隔: {self.delay} 秒")
        print(f"PDF下载: {'启用' if self.download_pdf else '禁用'}")
        print(f"PDF目录: {self.pdf_dir}/")
        print("=" * 70)

        papers_by_category = {}
        download_results = {}

        for i, category in enumerate(categories):
            # 1. 获取RSS
            papers = self.fetch_rss_feed(category)
            papers_by_category[category] = papers

            # 2. 下载PDF（如果启用且有论文）
            if self.download_pdf and papers:
                paper = papers[0]
                print(f"  📄 准备下载PDF: {paper['arxiv_id']}")
                success, path, size = self.download_pdf_file(paper, category)
                download_results[category] = (success, path, size)
            else:
                download_results[category] = (False, "无论文或已禁用", 0)

            # 3. 间隔等待
            if i < len(categories) - 1 and self.delay > 0:
                print(f"  ⏳ 等待 {self.delay} 秒...")
                time.sleep(self.delay)

        print("=" * 70)
        print("正在生成 Markdown 报告...")

        # 生成并保存
        md_content = self.generate_markdown(papers_by_category, download_results)
        filename = self.save_markdown(md_content)

        # 打印摘要
        print("\n" + "=" * 70)
        print("获取摘要:")
        print("-" * 70)

        for cat in categories:
            papers = papers_by_category.get(cat, [])
            success, path, size = download_results.get(cat, (False, "未下载", 0))

            if papers:
                p = papers[0]
                title = p['title'][:45] + '...' if len(p['title']) > 45 else p['title']
                print(f"  ✓ {cat:10s} | {title}")
                if success:
                    print(f"    PDF: {self._format_size(size):>10s} | {path}")
                else:
                    print(f"    PDF: 下载失败 - {path}")
            else:
                print(f"  ✗ {cat:10s} | 今日无新论文")

        print("=" * 70)

        return filename, papers_by_category, download_results


# ==================== 主程序 ====================

if __name__ == "__main__":
    # 指定分类列表
    TARGET_CATEGORIES = [
        'cs.AI',  # 人工智能
        #'cs.CC',  # 计算复杂性
        #'math.AG',  # 代数几何
        #'math.NT',  # 数论
        #'cs.ET',  # 新兴技术
        #'cs.GL',  # 一般文献
        #'cs.IT',  # 信息论
    ]

    # 配置参数
    CONFIG = {
        'delay': 5,  # 请求间隔（秒）
        'download_pdf': True,  # 是否下载PDF
        'pdf_dir': 'arxiv_pdfs'  # PDF保存目录
    }

    # 创建获取器并运行
    fetcher = ArxivRSSFetcher(**CONFIG)
    filename, results, downloads = fetcher.run(TARGET_CATEGORIES)

    # 最终报告
    print(f"\n🎉 全部完成！")
    print(f"   Markdown报告: {filename}")
    print(f"   PDF文件目录: {CONFIG['pdf_dir']}/")

    # 统计
    total_pdfs = sum(1 for s, _, _ in downloads.values() if s)
    print(f"   PDF下载成功: {total_pdfs}/{len(TARGET_CATEGORIES)}")

    if total_pdfs > 0:
        print(f"\n💡 提示:")
        print(f"   PDF文件按分类存储在 {CONFIG['pdf_dir']}/<分类名>/ 目录下")
        print(f"   例如: {CONFIG['pdf_dir']}/cs.AI/2501.12345.pdf")