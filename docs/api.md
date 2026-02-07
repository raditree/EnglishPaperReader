# 🔌 API 文档

> **版本**: v1.0.0  
> **作者**: [raditree](https://github.com/raditree)  
> **开源协议**: [MIT License](../LICENSE)

本文档描述 Paper Reader 后端提供的 RESTful API 接口。

## 基础信息

- **Base URL**: `http://localhost:8603`
- **Stats URL**: `http://localhost:8605`
- **Content-Type**: `application/json`

---

## 页面路由

### 阅读器主页

```
GET /
```

返回阅读器 HTML 页面。

### 统计页面

```
GET /stats
```

返回统计数据 HTML 页面。

---

## 论文相关

### 获取论文列表

```
GET /api/papers
```

返回所有可用的 PDF 论文列表。

**Response:**
```json
[
  {
    "id": "2501.12345",
    "category": "cs.AI",
    "filename": "2501.12345.pdf",
    "path": "cs.AI/2501.12345.pdf"
  }
]
```

### 获取 PDF 文件

```
GET /api/paper/<path:filename>
```

返回指定 PDF 文件内容。

**Parameters:**
| 参数 | 类型 | 说明 |
|------|------|------|
| filename | string | PDF 文件路径，如 `cs.AI/2501.12345.pdf` |

---

## 翻译相关

### 翻译单词

```
POST /api/translate
```

翻译指定单词并记录查询历史。

**Request Body:**
```json
{
  "word": "algorithm",
  "context": "The algorithm runs in O(n log n) time",
  "session_id": "session_123456",
  "paper_id": "2501.12345",
  "category": "cs.AI"
}
```

**Parameters:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| word | string | ✅ | 要翻译的单词 |
| context | string | ❌ | 上下文句子 |
| session_id | string | ❌ | 会话ID |
| paper_id | string | ❌ | 论文ID |
| category | string | ❌ | 论文分类 |

**Response:**
```json
{
  "word": "algorithm",
  "translation": "音标：/ˈælɡərɪðəm/。释义：n. [计] 算法；计算程序",
  "context": "The algorithm runs in O(n log n) time"
}
```

---

## 会话管理

### 开始阅读会话

```
POST /api/session/start
```

开始一个新的阅读会话，用于追踪阅读时长和查询记录。

**Request Body:**
```json
{
  "session_id": "session_123456",
  "paper_id": "2501.12345",
  "category": "cs.AI"
}
```

**Parameters:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| session_id | string | ❌ | 会话ID，不传则自动生成 |
| paper_id | string | ❌ | 论文ID |
| category | string | ❌ | 论文分类 |

**Response:**
```json
{
  "session_id": "session_123456",
  "status": "started"
}
```

### 结束阅读会话

```
POST /api/session/end
```

结束阅读会话并计算统计数据。

**Request Body:**
```json
{
  "session_id": "session_123456",
  "duration_seconds": 1800
}
```

**Parameters:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| session_id | string | ✅ | 会话ID |
| duration_seconds | integer | ❌ | 阅读时长（秒） |

**Response:**
```json
{
  "status": "ended",
  "session_id": "session_123456"
}
```

---

## 统计查询

### 每日统计

```
GET /api/daily?days=30
```

获取最近 N 天的学习统计数据。

**Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days | integer | 30 | 查询天数 |

**Response:**
```json
[
  {
    "date": "2026-02-06",
    "total_papers_read": 3,
    "total_words_queried": 42,
    "unique_words": 25,
    "repeat_query_rate": 40.5,
    "avg_queries_per_paper": 14.0,
    "total_reading_time": 2700,
    "vocabulary_size": 156,
    "category_distribution": "{\"cs.AI\": 32, \"cs.CC\": 10}"
  }
]
```

### 通用统计查询

```
GET /api/stats/<query_type>?param1=value1&...
```

支持多种类型的统计查询。

**Query Types:**

#### 1. 单词频率统计

```
GET /api/stats/word_frequency?days=7&limit=20
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days | integer | 7 | 查询天数 |
| limit | integer | 20 | 返回数量 |

**Response:**
```json
{
  "words": [
    {
      "word": "algorithm",
      "count": 1,
      "total": 5
    }
  ]
}
```

#### 2. 学习曲线

```
GET /api/stats/learning_curve?days=30
```

**Response:**
```json
{
  "daily_data": [
    {
      "date": "2026-02-06",
      "unique_words": 25,
      "vocabulary_size": 156,
      "total_words_queried": 42,
      "repeat_query_rate": 40.5
    }
  ]
}
```

#### 3. 分类统计

```
GET /api/stats/category_stats
```

**Response:**
```json
{
  "categories": [
    {
      "category": "cs.AI",
      "papers": 5,
      "queries": 32,
      "unique_words": 20
    }
  ]
}
```

#### 4. 掌握度分布

```
GET /api/stats/mastery_distribution
```

**Response:**
```json
{
  "distribution": [
    {
      "mastery_level": 0,
      "count": 50
    },
    {
      "mastery_level": 1,
      "count": 30
    }
  ]
}
```

掌握度等级：
- 0: 新词（查询1次）
- 1-4: 复习中
- 5: 已掌握

#### 5. 复习建议

```
GET /api/stats/review_suggestions?limit=20
```

根据艾宾浩斯遗忘曲线返回建议复习的单词。

**Response:**
```json
{
  "suggestions": [
    {
      "word": "algorithm",
      "query_count": 3,
      "first_seen": "2026-02-01",
      "last_seen": "2026-02-05",
      "review_count": 2,
      "days_since": 1
    }
  ]
}
```

#### 6. 会话详情

```
GET /api/stats/session_detail?session_id=xxx
```

**Response:**
```json
{
  "session": {
    "session_id": "session_123456",
    "paper_id": "2501.12345",
    "category": "cs.AI",
    "start_time": "2026-02-06 10:00:00",
    "end_time": "2026-02-06 10:30:00",
    "duration_seconds": 1800,
    "unique_words": 15,
    "total_queries": 20,
    "words": [
      {
        "word": "algorithm",
        "translation": "...",
        "context": "...",
        "query_count": 2
      }
    ]
  }
}
```

#### 7. 单词历史

```
GET /api/stats/word_history?word=algorithm
```

查询指定单词的查询历史。

**Response:**
```json
{
  "history": [
    {
      "query_time": "2026-02-06 10:15:30",
      "context": "The algorithm is efficient",
      "translation": "...",
      "paper_id": "2501.12345",
      "category": "cs.AI"
    }
  ]
}
```

---

## 用户数据管理

### 导入熟词

```
POST /api/user/import-familiar
```

从文本中批量导入已掌握的单词。

**Request Body:**
```json
{
  "text": "machine learning algorithm neural network...",
  "source": "manual_import"
}
```

**Parameters:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| text | string | ✅ | 包含英文单词的文本 |
| source | string | ❌ | 来源标识 |

**Response:**
```json
{
  "success": true,
  "added": 42,
  "total_extracted": 50,
  "batch_id": "20260207_153022"
}
```

---

### 获取熟词列表

```
GET /api/user/familiar-words
```

返回所有熟词的单词列表。

**Response:**
```json
{
  "words": ["algorithm", "neural", "network"],
  "count": 3
}
```

---

### 获取熟词详情（分页+搜索）

```
GET /api/user/familiar-words/details?limit=50&offset=0&search=algo
```

支持分页和搜索的熟词详情查询。

**Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 100 | 每页数量 |
| offset | integer | 0 | 偏移量 |
| search | string | "" | 搜索关键词 |

**Response:**
```json
{
  "words": [
    {
      "word": "algorithm",
      "added_date": "2026-02-07 15:30:22",
      "source": "manual_import",
      "import_batch": "20260207_153022",
      "query_count": 5,
      "mastery_level": 5
    }
  ],
  "total": 1
}
```

---

### 获取导入批次列表

```
GET /api/user/import-batches
```

返回所有导入批次的历史记录。

**Response:**
```json
{
  "batches": [
    {
      "import_batch": "20260207_153022",
      "source": "manual_import",
      "added_date": "2026-02-07 15:30:22",
      "word_count": 42
    }
  ]
}
```

---

### 撤销导入

```
POST /api/user/undo-import/<batch_id>
```

撤销指定批次的导入，将单词从熟词中移除。

**Parameters:**
| 参数 | 类型 | 说明 |
|------|------|------|
| batch_id | string | 批次ID，从导入响应或批次列表获取 |

**Response:**
```json
{
  "success": true,
  "deleted": 42
}
```

---

## 错误处理

API 使用标准 HTTP 状态码：

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**Error Response:**
```json
{
  "error": "错误描述",
  "code": 400
}
```

---

## 代码示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8603"

# 获取论文列表
response = requests.get(f"{BASE_URL}/api/papers")
papers = response.json()

# 翻译单词
response = requests.post(f"{BASE_URL}/api/translate", json={
    "word": "algorithm",
    "context": "The algorithm runs fast",
    "paper_id": "2501.12345"
})
translation = response.json()

# 获取学习统计
response = requests.get(f"{BASE_URL}/api/daily?days=7")
stats = response.json()
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8603';

// 获取论文列表
fetch(`${BASE_URL}/api/papers`)
  .then(res => res.json())
  .then(papers => console.log(papers));

// 翻译单词
fetch(`${BASE_URL}/api/translate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    word: 'algorithm',
    context: 'The algorithm runs fast',
    paper_id: '2501.12345'
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```
