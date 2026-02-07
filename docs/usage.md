# 📖 使用指南
> **版本**: v1.0.0  
> **作者**: [raditree](https://github.com/raditree)  
> **开源协议**: [MIT License](../LICENSE)

## 目录
- [安装与启动](#安装与启动)
- [词典数据准备](#词典数据准备)
- [阅读论文](#阅读论文)
- [划词翻译](#划词翻译)
- [查看学习统计](#查看学习统计)
- [复习单词](#复习单词)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 安装与启动

### 1. 安装依赖

**Python 依赖：**
```bash
pip install -r requirements.txt
```

**前端依赖：**
前端依赖（PDF.js、Chart.js）通过 CDN 自动加载，无需手动安装。
如需离线使用，请参考[离线部署](#离线部署)章节。

### 2. 准备词典数据

本项目使用 [ECDICT](https://github.com/skywind3000/ECDICT) 作为词典数据源。

1. 下载 `ecdict.csv` 文件（约 100MB）
2. 将文件放到项目根目录
3. 构建 SQLite 数据库：

```python
from paper_reader.translate import ECDict

tool = ECDict()
tool.build_db()  # 首次运行需要 1-2 分钟
```

构建完成后会生成 `ecdict.db` 文件（约 60MB）。

### 3. 启动应用

```bash
cd paper_reader
python app.py
```

启动成功后会看到：
```
✓ 数据库初始化完成
📖 阅读器启动: http://localhost:8603
📊 统计服务器启动: http://localhost:8605
```

---

## 词典数据准备

### 下载 ECDICT

ECDICT 是一个免费开源的英汉词典数据库，包含：
- 50万+ 英文单词
- 音标、释义、词性
- 柯林斯星级、BNC/FRQ 词频
- 变形、例句等

下载地址：https://github.com/skywind3000/ECDICT/releases

### 构建词典数据库

```python
from paper_reader.translate import ECDict

tool = ECDict(csv_file="ecdict.csv", db_file="ecdict.db")

# 检查是否已构建
if not tool.is_built():
    print("正在构建词典数据库...")
    tool.build_db(batch_size=5000)
    print("构建完成！")
else:
    print("词典数据库已就绪")
```

---

## 阅读论文

### 打开阅读器

访问 http://localhost:8603 进入阅读器主页面。

### 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│  📚 Paper Reader                                    [用户]   │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ 分类列表  │              PDF 阅读区域                        │
│          │                                                  │
│ ▶ cs.AI  │                                                  │
│   ├ 📄   │                                                  │
│   ├ 📄   │                                                  │
│   └ 📄   │                                                  │
│          │                                                  │
│ ▶ cs.CC  │                                                  │
│ ▶ math   │                                                  │
│          │                                                  │
├──────────┴──────────────────────────────────────────────────┤
│ 状态栏: 当前论文 | 阅读时长 | 今日查询: 0 词                  │
└─────────────────────────────────────────────────────────────┘
```

### 阅读操作

1. **选择分类**：点击左侧分类展开论文列表
2. **打开论文**：点击论文标题加载 PDF
3. **翻页**：使用鼠标滚轮或页面导航按钮
4. **缩放**：使用工具栏的放大/缩小按钮

---

## 划词翻译

### 基本用法

1. 用鼠标选中 PDF 中的任意单词或短语
2. 松开鼠标后自动弹出翻译窗口
3. 查看翻译结果、音标、例句

### 翻译窗口

```
┌─────────────────────────────────────┐
│  🔍 翻译结果                    [×]  │
├─────────────────────────────────────┤
│  word: algorithm                    │
│  音标: /ˈælɡərɪðəm/                 │
│  词性: n.                           │
├─────────────────────────────────────┤
│  释义:                              │
│  1. [计] 算法                       │
│  2. 计算程序                        │
├─────────────────────────────────────┤
│  [📝 加入生词本]  [🔊 发音]         │
└─────────────────────────────────────┘
```

### 功能说明

| 功能 | 说明 |
|------|------|
| 划词翻译 | 选中单词即自动翻译 |
| 音标显示 | 显示英式/美式音标 |
| 词性标注 | 显示名词、动词等词性 |
| 柯林斯星级 | 显示单词常用程度（1-5星）|
| 自动记录 | 自动保存查询历史 |

---

## 查看学习统计

### 打开统计页面

访问 http://localhost:8605 查看学习统计数据。

### 统计面板

#### 1. 今日概览

```
┌─────────────────────────────────────────────────────┐
│  📊 今日学习概览                                      │
├─────────────┬─────────────┬─────────────┬───────────┤
│  阅读论文   │  查询单词   │  查询次数   │  阅读时长 │
│    3 篇    │   25 个    │    42 次   │  45 分钟  │
└─────────────┴─────────────┴─────────────┴───────────┘
```

#### 2. 学习曲线

显示最近 30 天的学习趋势：
- 每日查询单词数
- 词汇量增长曲线
- 重复查询率

#### 3. 分类统计

```
┌──────────────────────────────────────────────────┐
│  📚 分类阅读统计                                  │
├──────────────┬────────┬─────────┬──────────────┤
│   分类       │ 论文数 │ 查询数  │  平均查询/篇 │
├──────────────┼────────┼─────────┼──────────────┤
│  cs.AI       │   5    │   32    │     6.4     │
│  cs.CC       │   2    │   10    │     5.0     │
│  math.AG     │   1    │   8     │     8.0     │
└──────────────┴────────┴─────────┴──────────────┘
```

#### 4. 高频单词

显示近期查询频率最高的单词，帮助你了解自己的词汇盲区。

---

## 复习单词

### 艾宾浩斯遗忘曲线

系统根据艾宾浩斯遗忘曲线算法，智能推荐需要复习的单词：

| 复习次数 | 间隔时间 |
|---------|---------|
| 第1次    | 1天      |
| 第2次    | 2天      |
| 第3次    | 4天      |
| 第4次    | 7天      |
| 第5次    | 15天     |

### 复习建议

在统计页面查看"复习建议"板块：

```
┌──────────────────────────────────────────────────┐
│  📌 今日复习建议 (12 个单词)                      │
├──────────────────────────────────────────────────┤
│  algorithm    [3天前]   查询3次   [标记已复习]   │
│  polynomial   [2天前]   查询2次   [标记已复习]   │
│  entropy      [1天前]   查询5次   [标记已复习]   │
│  ...                                              │
└──────────────────────────────────────────────────┘
```

点击"标记已复习"更新复习进度。

---

## 配置说明

### 应用配置

编辑 `paper_reader/app.py` 修改配置：

```python
CONFIG = {
    # 服务器端口
    'READER_PORT': 8603,          # 阅读器端口
    'STATS_PORT': 8605,           # 统计页面端口
    
    # 数据存储路径
    'DB_PATH': 'db/reading_stats.db',   # 学习统计数据库
    'PDF_DIR': 'pdfs',                  # PDF 存储目录
    'LOG_DIR': 'log',                   # 日志目录
    
    # RSS 获取配置
    'fetcher': {
        'delay': 5,               # 请求间隔（秒）
        'download_pdf': True,     # 是否自动下载 PDF
        'pdf_dir': 'pdfs'         # PDF 保存目录
    }
}
```

### 订阅分类配置

编辑 `app.py` 中的 `categories` 列表：

```python
categories = [
    'cs.AI',      # 人工智能
    'cs.CC',      # 计算复杂性
    'cs.CL',      # 计算语言学
    'cs.CR',      # 密码学
    'cs.CV',      # 计算机视觉
    'cs.DB',      # 数据库
    'cs.DC',      # 分布式计算
    'cs.DS',      # 数据结构
    'cs.GT',      # 博弈论
    'cs.IR',      # 信息检索
    'cs.LG',      # 机器学习
    'cs.NI',      # 网络与互联网架构
    'cs.OS',      # 操作系统
    'cs.PL',      # 编程语言
    'cs.SE',      # 软件工程
    'math.AG',    # 代数几何
    'math.AT',    # 代数拓扑
    'math.CO',    # 组合数学
    'math.NT',    # 数论
    'math.PR',    # 概率论
    'math.ST',    # 统计学
    # ... 更多分类
]
```

arXiv 分类列表：https://arxiv.org/category_taxonomy

---

## 常见问题

### Q: 词典数据库构建失败

**A:** 检查以下几点：
1. 确保 `ecdict.csv` 文件存在且格式正确
2. 确保磁盘空间充足（需要约 100MB）
3. 尝试减小 `batch_size` 参数：
   ```python
   tool.build_db(batch_size=1000)
   ```

### Q: PDF 无法加载

**A:** 
1. 检查 `pdfs/` 目录是否存在对应文件
2. 检查浏览器控制台是否有跨域错误
3. 确保使用支持的浏览器（Chrome/Firefox/Edge）

### Q: 翻译功能不工作

**A:**
1. 检查 `ecdict.db` 是否存在
2. 检查浏览器控制台是否有网络错误
3. 重启应用服务

### Q: 如何手动获取论文

**A:** 运行以下代码：
```python
from paper_reader.get_passage import ArxivRSSFetcher

fetcher = ArxivRSSFetcher(delay=5, download_pdf=True)
categories = ['cs.AI', 'cs.LG']
fetcher.run(categories)
```

### Q: 如何备份学习数据

**A:** 学习数据存储在 `db/reading_stats.db`，直接复制该文件即可备份。

### Q: 如何清空学习记录

**A:** 删除或重命名 `db/reading_stats.db` 文件，重启应用后会自动创建新数据库。

---

## 离线部署

如需在内网或离线环境使用，需要下载前端依赖到本地：

### 1. 下载 PDF.js

```bash
# 创建目录
mkdir -p paper_reader/static/lib/pdfjs

# 下载文件（需要网络）
curl -o paper_reader/static/lib/pdfjs/pdf.min.js \
  https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js

curl -o paper_reader/static/lib/pdfjs/pdf.worker.min.js \
  https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js

curl -o paper_reader/static/lib/pdfjs/pdf_viewer.min.css \
  https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css
```

### 2. 下载 Chart.js

```bash
mkdir -p paper_reader/static/lib/chartjs

curl -o paper_reader/static/lib/chartjs/chart.umd.min.js \
  https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js
```

### 3. 修改模板引用

编辑 `paper_reader/templates/reader.html`：

```html
<!-- 替换前 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>

<!-- 替换后 -->
<script src="{{ url_for('static', filename='lib/pdfjs/pdf.min.js') }}"></script>
```

编辑 `paper_reader/templates/stats.html`：

```html
<!-- 替换前 -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- 替换后 -->
<script src="{{ url_for('static', filename='lib/chartjs/chart.umd.min.js') }}"></script>
```

---

## 下一步

- 查看 [API 文档](api.md) 了解后端接口
- 查看 [开发说明](development.md) 了解如何扩展功能
