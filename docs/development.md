# 🔧 开发说明

> **版本**: v1.0.0  
> **作者**: [raditree](https://github.com/raditree)  
> **开源协议**: [MIT License](../LICENSE)  
> **最后更新**: 2026-02-07

本文档面向开发者，介绍项目架构、扩展方法和开发规范。

---

## 📑 目录

- [项目概览](#项目概览)
- [项目架构](#项目架构)
- [模块说明](#模块说明)
- [数据库结构](#数据库结构)
- [扩展开发](#扩展开发)
- [开发规范](#开发规范)
- [API 参考](#api-参考)
- [部署指南](#部署指南)
- [贡献指南](#贡献指南)

---

## 🎯 项目概览

**项目名称**: Paper Reading While English Learning  
**功能**: 结合 arXiv 论文阅读与英语学习的 Web 应用  
**技术栈**: Python + Flask + SQLite + PDF.js + Chart.js

---

## 🏗️ 项目架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Frontend)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  reader.html│  │  stats.html │  │  CSS/JS             │  │
│  │  阅读器界面  │  │  统计界面   │  │  样式与交互          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 层 (Flask Routes)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  /api/paper │  │ /api/translate│  │  /api/stats/*     │  │
│  │  论文服务    │  │  翻译服务    │  │  统计服务          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                       └── routes.py                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Services)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ ArxivDownloader│  │ BatchTranslator│  │ DatabaseManager│  │
│  │  arXiv下载   │  │ 批量翻译器   │  │  数据库管理        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   ECDict    │  │ ArxivRSSFetcher│  │  StatsService    │  │
│  │  词典查询    │  │  RSS获取器   │  │  统计服务          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (Data Layer)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  ecdict.db  │  │reading_stats│  │   PDF Files         │  │
│  │  词典数据库  │  │    .db      │  │   论文文件         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 文件结构 (v1.0.0)

```
paper_reader/
├── __init__.py          # 包初始化
├── app.py               # 应用入口 (40行，精简版)
├── config.py            # 配置管理
├── constants.py         # 常量定义
├── utils.py             # 工具函数
├── database.py          # 数据库管理 (DatabaseManager)
├── downloaders.py       # arXiv下载器 (ArxivDownloader)
├── translators.py       # 翻译模块
├── routes.py            # API路由
├── stats_service.py     # 统计服务
├── batch_translator.py  # 批量翻译器
├── get_passage.py       # RSS获取器
├── translate.py         # ECDict词典
├── templates/           # HTML模板
│   ├── reader.html
│   └── stats.html
├── static/              # 静态资源
│   ├── css/
│   └── js/
├── db/                  # SQLite数据库
├── pdfs/                # PDF文件
└── log/                 # 日志文件
```

---

## 📦 模块说明

### 1. app.py

**职责**: Flask应用主入口

**特点**: 
- 代码精简至 40 行（原 1806 行已拆分）
- 仅负责启动应用和初始化配置

```python
from routes import app
from stats_service import start_background_services, start_main_server

if __name__ == "__main__":
    enable_background_fetch = "--fetch" in sys.argv
    start_background_services(enable_fetch=enable_background_fetch)
    start_main_server()
```

---

### 2. config.py

**职责**: 集中管理所有配置参数

```python
# 配置示例
CONFIG = {
    "READER_PORT": 8603,
    "STATS_PORT": 8605,
    "DB_PATH": "db/reading_stats.db",
    "PDF_DIR": "pdfs",
    "LOG_DIR": "log",
}
```

**设计原则**:
- 所有路径使用绝对路径
- 支持环境变量覆盖
- 配置项分类清晰

---

### 3. database.py

**职责**: 数据库管理器 (DatabaseManager)

**核心功能**:
- 数据库初始化和迁移
- CRUD 操作封装
- 统计查询接口

```python
class DatabaseManager:
    def record_word_query(word, context, ...)  # 记录单词查询
    def start_session(session_id, ...)         # 开始阅读会话
    def end_session(session_id, ...)           # 结束阅读会话
    def query_stats(query_type, ...)           # 统计查询
    def migrate_database()                     # 数据库迁移
```

**数据库表**:
- `papers` - 论文信息
- `word_queries` - 单词查询记录
- `reading_sessions` - 阅读会话
- `daily_stats` - 每日统计
- `word_mastery` - 单词掌握度
- `familiar_words` - 熟词表

---

### 4. downloaders.py

**职责**: arXiv论文下载器 (ArxivDownloader)

```python
class ArxivDownloader:
    @staticmethod
    def search_papers(query, max_results=10)     # 搜索论文
    def get_paper_by_id(arxiv_id)               # 通过ID获取
    def download_pdf(arxiv_id, category)        # 下载PDF
    def get_latest_papers(categories)           # 获取最新论文
```

**特性**:
- 支持 SSL 证书处理
- 备用下载方案（requests）
- 自动分类存储

---

### 5. translators.py

**职责**: 翻译模块

```python
# 全局批量翻译器
batch_translator = None

def get_global_batch_translator():
    """获取/初始化批量翻译器"""
    
def call_translator(word, context=""):
    """调用翻译接口（优先使用缓存）"""
```

**翻译流程**:
1. 尝试批量翻译器缓存
2. 失败则使用 ECDict 本地词典
3. 返回格式化翻译结果

---

### 6. routes.py

**职责**: API路由定义

**路由分类**:

| 路由 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 阅读器主页面 |
| `/stats` | GET | 统计页面 |
| `/api/papers` | GET | 获取本地论文列表 |
| `/api/papers/search` | POST | 搜索论文 |
| `/api/papers/download` | POST | 下载论文 |
| `/api/translate` | POST | 翻译单词 |
| `/api/translate/batch` | POST | 批量翻译 |
| `/api/stats/<type>` | GET | 统计查询 |
| `/api/session/start` | POST | 开始阅读会话 |
| `/api/session/end` | POST | 结束阅读会话 |

---

### 7. stats_service.py

**职责**: 后台服务和统计服务器

```python
def background_fetcher():
    """后台自动获取论文（每6小时）"""

def run_stats_server():
    """在8605端口运行统计服务器"""

def start_background_services(enable_fetch=False):
    """启动后台服务"""
```

---

### 8. batch_translator.py

**职责**: 批量翻译器，带缓存机制

```python
class BatchTranslator:
    def translate(self, word)                    # 翻译单个单词
    def batch_translate(self, words)            # 批量翻译
    def extract_words_from_text(self, text)     # 从文本提取单词
    def get_cache_stats(self)                   # 获取缓存统计
    def clear_cache(self)                       # 清空缓存
```

---

## 🗄️ 数据库结构

### 1. reading_stats.db (学习统计数据库)

#### word_queries (单词查询记录)
```sql
CREATE TABLE word_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,              -- 查询的单词
    context TEXT,                    -- 上下文
    translation TEXT,                -- 翻译结果
    paper_id TEXT,                   -- 论文ID
    category TEXT,                   -- 论文分类
    query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_count INTEGER DEFAULT 1,   -- 查询次数
    session_id TEXT,                 -- 会话ID
    last_query_time TIMESTAMP
);
```

#### reading_sessions (阅读会话)
```sql
CREATE TABLE reading_sessions (
    session_id TEXT PRIMARY KEY,
    paper_id TEXT,
    category TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_words INTEGER DEFAULT 0,
    unique_words INTEGER DEFAULT 0,
    total_queries INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    pages_read INTEGER DEFAULT 0
);
```

#### daily_stats (每日统计)
```sql
CREATE TABLE daily_stats (
    date TEXT PRIMARY KEY,
    total_papers_read INTEGER DEFAULT 0,
    total_words_queried INTEGER DEFAULT 0,
    unique_words INTEGER DEFAULT 0,
    repeat_query_rate REAL DEFAULT 0.0,
    avg_queries_per_paper REAL DEFAULT 0.0,
    total_reading_time INTEGER DEFAULT 0,
    vocabulary_size INTEGER DEFAULT 0,
    category_distribution TEXT,        -- JSON格式
    new_words INTEGER DEFAULT 0,
    mastered_words INTEGER DEFAULT 0,
    papers_downloaded INTEGER DEFAULT 0
);
```

#### word_mastery (单词掌握度)
```sql
CREATE TABLE word_mastery (
    word TEXT PRIMARY KEY,
    query_count INTEGER DEFAULT 0,
    first_seen DATE,
    last_seen DATE,
    mastery_level INTEGER DEFAULT 0,  -- 0-5级
    review_count INTEGER DEFAULT 0,
    consecutive_correct INTEGER DEFAULT 0,
    is_familiar INTEGER DEFAULT 0,
    is_mastered INTEGER DEFAULT 0,
    notes TEXT
);
```

### 2. ecdict.db (词典数据库)

```sql
CREATE TABLE words (
    word TEXT PRIMARY KEY,
    phonetic TEXT,          -- 音标
    definition TEXT,        -- 英文释义
    translation TEXT,       -- 中文翻译
    pos TEXT,               -- 词性
    collins INTEGER,        -- 柯林斯星级
    oxford INTEGER,         -- 牛津核心词汇
    tag TEXT,               -- 标签
    bnc INTEGER,            -- BNC词频
    frq INTEGER,            -- 现代词频
    exchange TEXT,          -- 变形
    detail TEXT,            -- 详细释义
    audio TEXT              -- 音频链接
);
```

---

## 🧩 扩展开发

### 1. 添加新的数据源

以添加 IEEE Xplore 为例：

```python
# paper_reader/ieee_fetcher.py

import requests
from datetime import datetime

class IEEEFetcher:
    """IEEE Xplore 论文获取器"""
    
    def __init__(self, api_key, delay=5):
        self.api_key = api_key
        self.delay = delay
        self.base_url = "http://ieeexploreapi.ieee.org/api/v1/search/articles"
    
    def search(self, query, max_results=10):
        """搜索论文"""
        params = {
            'apikey': self.api_key,
            'querytext': query,
            'max_results': max_results,
            'format': 'json'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def download_pdf(self, article_id, save_path):
        """下载 PDF"""
        # 实现下载逻辑
        pass
```

集成到 `stats_service.py`：

```python
from ieee_fetcher import IEEEFetcher

def background_ieee_fetcher():
    fetcher = IEEEFetcher(CONFIG['ieee']['api_key'])
    while True:
        papers = fetcher.search('machine learning', max_results=5)
        # 处理论文...
        time.sleep(24 * 3600)  # 每天获取一次
```

---

### 2. 添加新的翻译服务

以添加有道翻译 API 为例：

```python
# paper_reader/translators/youdao.py

import requests
import hashlib
import time
import random

class YoudaoTranslator:
    """有道翻译 API"""
    
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.url = "https://openapi.youdao.com/api"
    
    def translate(self, text, from_lang='en', to_lang='zh-CHS'):
        """翻译文本"""
        salt = random.randint(1, 65536)
        sign_str = self.app_key + text + str(salt) + self.app_secret
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        data = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appKey': self.app_key,
            'salt': salt,
            'sign': sign
        }
        
        response = requests.post(self.url, data=data)
        return response.json()
```

修改 `translators.py`：

```python
from translators.youdao import YoudaoTranslator

def call_translator(word, context=''):
    """调用翻译接口（支持多源）"""
    
    # 1. 首先尝试本地词典
    translator = get_global_batch_translator()
    result = translator.translate(word)
    
    # 2. 如果本地未找到，调用有道 API
    if result.translation.startswith("[翻译错误]"):
        youdao = YoudaoTranslator(app_key, app_secret)
        api_result = youdao.translate(word)
        return format_youdao_result(api_result)
    
    return result.translation
```

---

### 3. 添加新的统计图表

在 `stats.html` 中添加新图表：

```html
<!-- 热力图容器 -->
<div id="heatmap-chart" style="width: 100%; height: 300px;"></div>
```

在 `stats.js` 中添加：

```javascript
// 加载热力图数据
async function loadHeatmapData() {
    const response = await fetch('/api/stats/heatmap?year=2026');
    const data = await response.json();
    
    // 使用 ECharts 渲染
    const chart = echarts.init(document.getElementById('heatmap-chart'));
    const option = {
        title: { text: '学习热力图' },
        visualMap: { min: 0, max: 100 },
        calendar: { range: '2026' },
        series: [{
            type: 'heatmap',
            coordinateSystem: 'calendar',
            data: data.heatmap
        }]
    };
    chart.setOption(option);
}
```

在 `routes.py` 中添加接口：

```python
@app.route('/api/stats/heatmap')
@error_handler
def get_heatmap_data():
    """获取学习热力图数据"""
    year = request.args.get('year', datetime.now().year, type=int)
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DATE(query_time) as date, COUNT(*) as count
        FROM word_queries
        WHERE strftime('%Y', query_time) = ?
        GROUP BY DATE(query_time)
    ''', (str(year),))
    
    data = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'heatmap': [[row['date'], row['count']] for row in data]
    })
```

---

## 📋 开发规范

### 代码风格

1. **遵循 PEP 8**
   - 使用 4 空格缩进
   - 行长度不超过 100 字符
   - 函数和变量使用小写+下划线命名

2. **文档字符串 (Google Style)**
   ```python
   def function_name(param1, param2):
       """
       函数简要说明
       
       Args:
           param1: 参数1说明
           param2: 参数2说明
           
       Returns:
           返回值说明
           
       Raises:
           ValueError: 异常说明
       """
       pass
   ```

3. **类型注解**
   ```python
   from typing import Optional, List, Dict, Any
   
   def search(word: str, limit: int = 10) -> Optional[Dict[str, Any]]:
       pass
   ```

### Git 提交规范

1. **提交信息格式**
   ```
   <type>: <subject>
   
   <body>
   
   <footer>
   ```

2. **Type 类型**
   - `feat`: 新功能
   - `fix`: 修复
   - `docs`: 文档
   - `style`: 格式调整
   - `refactor`: 重构
   - `test`: 测试
   - `chore`: 构建/工具

3. **示例**
   ```
   feat: 添加 IEEE 论文源支持
   
   - 实现 IEEEFetcher 类
   - 添加配置项
   - 更新文档
   
   Closes #123
   ```

---

## 📚 API 参考

### 论文相关 API

#### 获取本地论文列表
```http
GET /api/papers
```

#### 搜索论文
```http
POST /api/papers/search
Content-Type: application/json

{
    "query": "machine learning",
    "category": "cs.AI",
    "max_results": 10
}
```

#### 下载论文
```http
POST /api/papers/download
Content-Type: application/json

{
    "arxiv_id": "2401.12345",
    "category": "cs.AI"
}
```

### 翻译相关 API

#### 翻译单词
```http
POST /api/translate
Content-Type: application/json

{
    "word": "algorithm",
    "context": "This algorithm is efficient",
    "session_id": "123456",
    "paper_id": "2401.12345"
}
```

#### 批量翻译
```http
POST /api/translate/batch
Content-Type: application/json

{
    "words": ["algorithm", "neural", "network"]
}
```

### 统计相关 API

#### 获取每日统计
```http
GET /api/daily?days=30
```

#### 统计查询
```http
GET /api/stats/word_frequency?days=7&limit=20
GET /api/stats/learning_curve?days=30
GET /api/stats/category_stats
```

---

## 🚀 部署指南

### 生产环境部署

1. **使用 Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8603 "paper_reader.app:app"
   ```

2. **使用 Nginx 反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8603;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **使用 Supervisor 管理进程**
   ```ini
   [program:paper-reader]
   command=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8603 "paper_reader.app:app"
   directory=/path/to/paper_reader
   user=www-data
   autostart=true
   autorestart=true
   ```

---

## 🤝 贡献指南

### 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'feat: xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

### 代码审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 包含适当的文档字符串
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过所有测试

### 报告问题

请使用 GitHub Issues 报告问题，并包含以下信息：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（OS, Python 版本等）

---

## 📄 许可证

本项目采用 [MIT License](../LICENSE) 开源协议。

```
MIT License

Copyright (c) 2026 raditree

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 联系方式

- **作者**: [raditree](https://github.com/raditree)
- **项目主页**: [GitHub Repository](https://github.com/raditree/EnglishPaperReader)
- **问题反馈**: [GitHub Issues](https://github.com/raditree/EnglishPaperReader/issues)

---

**Made with ❤️ by raditree**  
**Version: v1.0.0**
