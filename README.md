# 📚 Paper Reading While English Learning

> **版本**: v1.1.0  
> **作者**: [raditree](https://github.com/raditree)  
> **开源协议**: [MIT License](./LICENSE)

边读论文边学英语 - 一个结合 arXiv 论文阅读与英语学习的 Web 应用。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![PDF.js](https://img.shields.io/badge/PDF.js-3.11.174-orange.svg)](https://mozilla.github.io/pdf.js)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-red.svg)](https://www.chartjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## ✨ 功能特性

### 📖 论文阅读
- 自动从 arXiv RSS 获取最新论文
- 支持多分类订阅（AI、CC、Math 等）
- 自动下载 PDF 到本地分类存储
- 基于 PDF.js 的 Web 端 PDF 阅读器
- 护眼模式（色温/亮度调节、夜间模式）

### 🔤 划词翻译
- 基于 ECDICT 的本地英汉词典（50万+单词）
- 支持划词即译，快捷键翻译 (Ctrl+M / ⌘+M)
- 单词本功能，自动记录查询历史
- 支持模糊搜索和中文反向查询
- 批量翻译缓存，提升阅读体验

### 📊 学习统计
- 实时记录阅读时长和单词查询
- 每日学习数据统计（查询次数、词汇量等）
- 单词掌握度追踪（0-5级）
- 基于艾宾浩斯遗忘曲线的复习建议
- 分类阅读统计（不同学科领域）
- 可视化图表（Chart.js）
- **熟词导入**：从文本或文件批量导入已掌握的单词
- **导入撤销**：支持撤销错误的导入批次，自动还原单词状态
- **词库管理**：查看所有熟词，支持搜索和分页浏览

### 🔄 自动化
- 后台每6小时自动获取最新论文
- 自动去重，避免重复下载
- 生成每日论文精选 Markdown 报告

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- ECDICT 词典文件（`ecdict.csv`）
- 网络连接（用于 CDN 资源）

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/raditree/EnglishPaperReader.git
cd EnglishPaperReader
```

2. **安装 Python 依赖**
```bash
pip install -r requirements.txt
```

3. **准备词典文件**

下载 ECDICT 词典文件 `ecdict.csv` 放到项目根目录，然后构建数据库：

```bash
# 下载词典（约 30MB）
# 地址：https://github.com/skywind3000/ECDICT/releases

# 构建数据库
python -c "from paper_reader.translate import ECDict; ECDict().build_db()"
```

4. **启动应用**
```bash
cd paper_reader
python app.py
```

5. **访问应用**
- 阅读器：http://localhost:8603
- 统计页面：http://localhost:8605

---

## 📁 项目结构

```
EnglishPaperReader/
├── paper_reader/              # 主应用目录
│   ├── __init__.py            # 包初始化
│   ├── app.py                 # 应用入口（精简版，40行）
│   ├── config.py              # 配置管理
│   ├── constants.py           # 常量定义
│   ├── utils.py               # 工具函数
│   ├── database.py            # 数据库管理
│   ├── downloaders.py         # arXiv下载器
│   ├── translators.py         # 翻译模块
│   ├── routes.py              # API路由
│   ├── stats_service.py       # 统计服务
│   ├── batch_translator.py    # 批量翻译器
│   ├── get_passage.py         # RSS获取器
│   ├── translate.py           # ECDict词典
│   ├── templates/             # HTML模板
│   │   ├── reader.html        # 阅读器页面（PDF.js）
│   │   └── stats.html         # 统计页面（Chart.js）
│   └── static/                # 静态资源
│       ├── css/
│       │   ├── reader.css
│       │   └── stats.css
│       └── js/
│           ├── reader.js      # PDF阅读器逻辑
│           └── stats.js       # 统计图表逻辑
├── pdfs/                      # PDF文件存储目录
├── db/                        # SQLite数据库
├── log/                       # 日志文件
├── docs/                      # 使用文档
│   ├── development.md         # 开发说明
│   ├── usage.md               # 使用指南
│   ├── api.md                 # API文档
│   └── CHANGELOG.md           # 更新日志
├── requirements.txt           # Python依赖
├── LICENSE                    # MIT许可证
└── README.md                  # 项目说明
```

---

## 🌐 前端依赖（CDN）

本项目前端依赖通过 CDN 引入，无需本地安装：

| 依赖 | 版本 | CDN |
|------|------|-----|
| PDF.js | 3.11.174 | cdnjs.cloudflare.com |
| Chart.js | 4.x | cdn.jsdelivr.net |

如需离线使用，可下载对应文件到 `static/lib/` 目录并修改模板引用。

---

## ⚙️ 配置说明

编辑 `paper_reader/config.py`：

```python
CONFIG = {
    'READER_PORT': 8603,          # 阅读器端口
    'STATS_PORT': 8605,           # 统计页面端口
    'DB_PATH': 'db/reading_stats.db',
    'PDF_DIR': 'pdfs',
    'LOG_DIR': 'log',
    'TEMPLATE_DIR': 'templates',
    'STATIC_DIR': 'static',
}

FETCHER_CONFIG = {
    'delay': 5,                   # RSS请求间隔（秒）
    'download_pdf': True,         # 是否自动下载PDF
    'pdf_dir': 'pdfs'
}
```

---

## 📝 使用指南

### 阅读论文
1. 打开 http://localhost:8603
2. 从下拉菜单选择论文
3. 使用鼠标滚轮翻页
4. 选中任意单词，按 `Ctrl+M` 翻译

### 护眼设置
- **色温调节**：拖动"色温"滑块（冷色/暖色）
- **亮度调节**：拖动"亮度"滑块
- **主题切换**：点击 🌙 按钮切换日间/夜间/护眼模式

### 查看统计
1. 打开 http://localhost:8605
2. 查看今日学习数据
3. 浏览词汇学习曲线
4. 查看复习建议

### 管理熟词词库
1. **导入熟词**：
   - 在统计页面点击「📥 导入熟词」
   - 粘贴包含英文单词的文本，或上传文本文件(.txt/.md/.csv)
   - 系统自动提取并标记为熟词，立即更新统计数据

2. **查看词库**：
   - 点击「📚 查看词库」浏览所有熟词
   - 支持实时搜索单词
   - 分页显示，每页50个单词

3. **撤销导入**：
   - 点击「📝 导入历史」查看所有导入批次
   - 发现错误导入可点击「撤销」按钮
   - 撤销后单词将从熟词中移除，统计数据自动更新

### 添加订阅分类
编辑 `stats_service.py` 中的 `background_fetcher` 函数：

```python
categories = [
    'cs.AI',    # 人工智能
    'cs.CC',    # 计算复杂性
    'cs.CL',    # 计算语言学
    # ... 更多分类
]
```

---

## 📚 文档

- [开发说明](docs/development.md) - 项目架构、模块说明、扩展开发
- [使用指南](docs/usage.md) - 详细使用教程
- [API 文档](docs/api.md) - API 接口参考
- [更新日志](docs/CHANGELOG.md) - 版本更新记录

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'feat: xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

### 开发规范
- 遵循 PEP 8 代码风格
- 使用 Google Style 文档字符串
- 提交信息遵循 `<type>: <subject>` 格式

详细规范请参考 [开发说明](docs/development.md#开发规范)。

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

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
```

---

## 🙏 致谢

- [ECDICT](https://github.com/skywind3000/ECDICT) - 开源英汉词典数据
- [PDF.js](https://github.com/mozilla/pdf.js) - Mozilla 开源 PDF 阅读器
- [Chart.js](https://www.chartjs.org/) - 开源图表库
- [arXiv](https://arxiv.org/) - 论文预印本平台
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架

---

## 📞 联系方式

- **作者**: [raditree](https://github.com/raditree)
- **项目主页**: [GitHub Repository](https://github.com/raditree/EnglishPaperReader)
- **问题反馈**: [GitHub Issues](https://github.com/raditree/EnglishPaperReader/issues)

---

**Made with ❤️ by raditree**  
**Version: v1.0.0**
