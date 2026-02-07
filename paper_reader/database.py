"""数据库管理模块 - 处理所有数据库操作"""

import sqlite3
import json
import os
from datetime import datetime
from config import CONFIG


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path=None):
        self.db_path = db_path or CONFIG["DB_PATH"]
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 论文信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                arxiv_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                categories TEXT,
                primary_category TEXT,
                published_date TEXT,
                updated_date TEXT,
                pdf_url TEXT,
                local_path TEXT,
                download_date TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                read_date TIMESTAMP,
                read_count INTEGER DEFAULT 0,
                last_read_time TIMESTAMP,
                word_count INTEGER DEFAULT 0,
                query_count INTEGER DEFAULT 0,
                UNIQUE(arxiv_id)
            )
        """)

        # 单词查询记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                context TEXT,
                translation TEXT,
                paper_id TEXT,
                category TEXT,
                query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                query_count INTEGER DEFAULT 1,
                session_id TEXT,
                last_query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers(arxiv_id)
            )
        """)

        # 阅读会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_sessions (
                session_id TEXT PRIMARY KEY,
                paper_id TEXT,
                category TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_words INTEGER DEFAULT 0,
                unique_words INTEGER DEFAULT 0,
                total_queries INTEGER DEFAULT 0,
                duration_seconds INTEGER DEFAULT 0,
                pages_read INTEGER DEFAULT 0,
                FOREIGN KEY (paper_id) REFERENCES papers(arxiv_id)
            )
        """)

        # 每日统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                total_papers_read INTEGER DEFAULT 0,
                total_words_queried INTEGER DEFAULT 0,
                unique_words INTEGER DEFAULT 0,
                repeat_query_rate REAL DEFAULT 0.0,
                avg_queries_per_paper REAL DEFAULT 0.0,
                total_reading_time INTEGER DEFAULT 0,
                vocabulary_size INTEGER DEFAULT 0,
                category_distribution TEXT,
                new_words INTEGER DEFAULT 0,
                mastered_words INTEGER DEFAULT 0,
                papers_downloaded INTEGER DEFAULT 0
            )
        """)

        # 单词掌握度表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_mastery (
                word TEXT PRIMARY KEY,
                query_count INTEGER DEFAULT 0,
                first_seen DATE,
                last_seen DATE,
                mastery_level INTEGER DEFAULT 0,
                review_count INTEGER DEFAULT 0,
                consecutive_correct INTEGER DEFAULT 0,
                is_familiar INTEGER DEFAULT 0,
                is_mastered INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        # 熟词表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS familiar_words (
                word TEXT PRIMARY KEY,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                import_batch TEXT
            )
        """)

        # 用户阅读偏好表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        # 执行数据库迁移（添加新列）
        self.migrate_database()

        print("✓ 数据库初始化完成")

    def migrate_database(self):
        """数据库迁移 - 添加新列"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 检查并添加 word_mastery 表的新列
        cursor.execute("PRAGMA table_info(word_mastery)")
        columns = [col["name"] for col in cursor.fetchall()]

        new_columns = {
            "is_familiar": "INTEGER DEFAULT 0",
            "is_mastered": "INTEGER DEFAULT 0",
            "consecutive_correct": "INTEGER DEFAULT 0",
            "notes": "TEXT",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE word_mastery ADD COLUMN {col_name} {col_type}"
                    )
                    print(f"  ✓ 添加列: word_mastery.{col_name}")
                except Exception as e:
                    print(f"  ⚠ 添加列失败 {col_name}: {e}")

        # 检查并添加 daily_stats 表的新列
        cursor.execute("PRAGMA table_info(daily_stats)")
        columns = [col["name"] for col in cursor.fetchall()]

        new_columns = {
            "new_words": "INTEGER DEFAULT 0",
            "mastered_words": "INTEGER DEFAULT 0",
            "papers_downloaded": "INTEGER DEFAULT 0",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE daily_stats ADD COLUMN {col_name} {col_type}"
                    )
                    print(f"  ✓ 添加列: daily_stats.{col_name}")
                except Exception as e:
                    print(f"  ⚠ 添加列失败 {col_name}: {e}")

        # 检查并添加 reading_sessions 表的新列
        cursor.execute("PRAGMA table_info(reading_sessions)")
        columns = [col["name"] for col in cursor.fetchall()]

        if "pages_read" not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE reading_sessions ADD COLUMN pages_read INTEGER DEFAULT 0"
                )
                print("  ✓ 添加列: reading_sessions.pages_read")
            except Exception as e:
                print(f"  ⚠ 添加列失败 pages_read: {e}")

        conn.commit()
        conn.close()

    def record_paper(
        self,
        arxiv_id,
        title,
        authors,
        abstract,
        categories,
        primary_category,
        published_date,
        pdf_url,
        local_path=None,
    ):
        """记录论文信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO papers 
            (arxiv_id, title, authors, abstract, categories, primary_category,
             published_date, pdf_url, local_path, download_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
            (
                arxiv_id,
                title,
                json.dumps(authors) if isinstance(authors, list) else authors,
                abstract,
                json.dumps(categories) if isinstance(categories, list) else categories,
                primary_category,
                published_date,
                pdf_url,
                local_path,
            ),
        )
        conn.commit()
        conn.close()

    def mark_paper_as_read(self, arxiv_id):
        """标记论文为已读"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE papers SET 
                is_read = 1, 
                read_date = COALESCE(read_date, CURRENT_TIMESTAMP),
                read_count = read_count + 1,
                last_read_time = CURRENT_TIMESTAMP
            WHERE arxiv_id = ?
        """,
            (arxiv_id,),
        )
        conn.commit()
        conn.close()

    def record_word_query(
        self,
        word,
        context=None,
        translation=None,
        paper_id=None,
        category=None,
        session_id=None,
    ):
        """记录单词查询"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()

        # 检查今日是否已查询过
        cursor.execute(
            """
            SELECT id, query_count FROM word_queries 
            WHERE word = ? AND DATE(query_time) = ? AND session_id = ?
        """,
            (word.lower(), today, session_id),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE word_queries 
                SET query_count = query_count + 1, 
                    last_query_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (existing["id"],),
            )
        else:
            cursor.execute(
                """
                INSERT INTO word_queries 
                (word, context, translation, paper_id, category, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (word.lower(), context, translation, paper_id, category, session_id),
            )

        # 更新单词掌握度
        cursor.execute(
            """
            INSERT INTO word_mastery (word, query_count, first_seen, last_seen, review_count)
            VALUES (?, 1, DATE('now'), DATE('now'), 1)
            ON CONFLICT(word) DO UPDATE SET
                query_count = query_count + 1,
                last_seen = DATE('now'),
                review_count = CASE 
                    WHEN DATE(word_mastery.last_seen) != DATE('now') 
                    THEN review_count + 1 
                    ELSE review_count 
                END
        """,
            (word.lower(),),
        )

        # 更新论文查询计数
        if paper_id:
            cursor.execute(
                """
                UPDATE papers SET query_count = query_count + 1
                WHERE arxiv_id = ?
            """,
                (paper_id,),
            )

        conn.commit()
        conn.close()

    def add_familiar_words(self, words, source="import"):
        """批量添加熟词，返回(添加数量, batch_id)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        added = 0
        for word in words:
            word = word.lower().strip()
            if word and len(word) > 1:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO familiar_words (word, source, import_batch)
                        VALUES (?, ?, ?)
                    """,
                        (word, source, batch_id),
                    )
                    # 同时在掌握度表中标记为熟悉
                    cursor.execute(
                        """
                        INSERT INTO word_mastery (word, is_familiar, mastery_level, first_seen, last_seen)
                        VALUES (?, 1, 5, DATE('now'), DATE('now'))
                        ON CONFLICT(word) DO UPDATE SET
                            is_familiar = 1,
                            mastery_level = 5
                    """,
                        (word,),
                    )
                    added += 1
                except:
                    pass
        conn.commit()
        conn.close()
        return added, batch_id

    def undo_import_batch(self, batch_id):
        """撤销指定批次的导入"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 获取该批次导入的所有单词
        cursor.execute(
            "SELECT word FROM familiar_words WHERE import_batch = ?", (batch_id,)
        )
        words = [row["word"] for row in cursor.fetchall()]

        # 删除该批次的熟词记录
        cursor.execute("DELETE FROM familiar_words WHERE import_batch = ?", (batch_id,))
        deleted_count = cursor.rowcount

        # 将这些单词从 word_mastery 中取消标记为熟悉
        for word in words:
            cursor.execute(
                """
                UPDATE word_mastery 
                SET is_familiar = 0, mastery_level = 0 
                WHERE word = ?
            """,
                (word,),
            )

        conn.commit()
        conn.close()
        return deleted_count

    def get_import_batches(self):
        """获取所有导入批次信息"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT import_batch, source, added_date, COUNT(*) as word_count
                FROM familiar_words
                GROUP BY import_batch
                ORDER BY added_date DESC
            """
            )
            batches = [dict(row) for row in cursor.fetchall()]
            return batches
        except Exception as e:
            print(f"[Database Error] get_import_batches: {e}")
            return []
        finally:
            conn.close()

    def get_familiar_words_with_details(self, limit=100, offset=0, search=""):
        """获取熟词列表及详细信息"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            if search:
                cursor.execute(
                    """
                    SELECT f.word, f.added_date, f.source, f.import_batch,
                           COALESCE(w.query_count, 0) as query_count,
                           COALESCE(w.mastery_level, 5) as mastery_level
                    FROM familiar_words f
                    LEFT JOIN word_mastery w ON f.word = w.word
                    WHERE f.word LIKE ?
                    ORDER BY f.added_date DESC
                    LIMIT ? OFFSET ?
                """,
                    (f"%{search}%", limit, offset),
                )
            else:
                cursor.execute(
                    """
                    SELECT f.word, f.added_date, f.source, f.import_batch,
                           COALESCE(w.query_count, 0) as query_count,
                           COALESCE(w.mastery_level, 5) as mastery_level
                    FROM familiar_words f
                    LEFT JOIN word_mastery w ON f.word = w.word
                    ORDER BY f.added_date DESC
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

            words = [dict(row) for row in cursor.fetchall()]

            # 获取总数
            if search:
                cursor.execute(
                    "SELECT COUNT(*) as total FROM familiar_words WHERE word LIKE ?",
                    (f"%{search}%",),
                )
            else:
                cursor.execute("SELECT COUNT(*) as total FROM familiar_words")

            total = cursor.fetchone()["total"]
            return {"words": words, "total": total}
        except Exception as e:
            print(f"[Database Error] get_familiar_words_with_details: {e}")
            return {"words": [], "total": 0}
        finally:
            conn.close()

    def get_familiar_words(self):
        """获取所有熟词"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM familiar_words")
        words = [row["word"] for row in cursor.fetchall()]
        conn.close()
        return words

    def get_papers(self, filters=None, limit=100, offset=0):
        """获取论文列表，支持筛选"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        if filters:
            if filters.get("category"):
                query += " AND primary_category = ?"
                params.append(filters["category"])
            if filters.get("is_read") is not None:
                query += " AND is_read = ?"
                params.append(1 if filters["is_read"] else 0)
            if filters.get("date_from"):
                query += " AND published_date >= ?"
                params.append(filters["date_from"])
            if filters.get("date_to"):
                query += " AND published_date <= ?"
                params.append(filters["date_to"])
            if filters.get("author"):
                query += " AND authors LIKE ?"
                params.append(f"%{filters['author']}%")
            if filters.get("search"):
                query += " AND (title LIKE ? OR arxiv_id LIKE ? OR abstract LIKE ?)"
                params.extend(
                    [
                        f"%{filters['search']}%",
                        f"%{filters['search']}%",
                        f"%{filters['search']}%",
                    ]
                )

        query += " ORDER BY published_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return papers

    def get_paper_by_id(self, arxiv_id):
        """通过ID获取论文"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def start_session(self, session_id, paper_id, category):
        """开始阅读会话"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO reading_sessions 
                (session_id, paper_id, category, start_time)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (session_id, paper_id, category),
            )
            conn.commit()
            # 标记论文为已读
            if paper_id:
                self.mark_paper_as_read(paper_id)
        except Exception as e:
            print(f"Session start error: {e}")
            raise
        finally:
            conn.close()

    def end_session(self, session_id, duration_seconds, pages_read=0):
        """结束阅读会话"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT word) as unique_words,
                       COUNT(*) as total_queries
                FROM word_queries
                WHERE session_id = ?
            """,
                (session_id,),
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                UPDATE reading_sessions
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = ?,
                    unique_words = ?,
                    total_queries = ?,
                    pages_read = ?
                WHERE session_id = ?
            """,
                (
                    duration_seconds,
                    stats["unique_words"] if stats else 0,
                    stats["total_queries"] if stats else 0,
                    pages_read,
                    session_id,
                ),
            )

            conn.commit()
        except Exception as e:
            print(f"Session end error: {e}")
            raise
        finally:
            conn.close()

        self.update_daily_stats()

    def update_daily_stats(self):
        """更新每日统计数据"""
        today = datetime.now().date().isoformat()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 今日查询统计
            cursor.execute(
                """
                SELECT COUNT(DISTINCT session_id) as papers,
                       COUNT(*) as total_queries,
                       COUNT(DISTINCT word) as unique_words,
                       SUM(CASE WHEN query_count > 1 THEN 1 ELSE 0 END) as repeat_queries
                FROM word_queries
                WHERE DATE(query_time) = ?
            """,
                (today,),
            )
            today_data = cursor.fetchone()

            repeat_rate = (
                (today_data["repeat_queries"] / today_data["total_queries"] * 100)
                if today_data["total_queries"] > 0
                else 0.0
            )
            avg_queries = (
                (today_data["total_queries"] / today_data["papers"])
                if today_data["papers"] > 0
                else 0.0
            )

            # 分类分布
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM word_queries
                WHERE DATE(query_time) = ? AND category IS NOT NULL
                GROUP BY category
            """,
                (today,),
            )
            category_dist = {row["category"]: row["count"] for row in cursor.fetchall()}

            # 词汇量统计
            cursor.execute("SELECT COUNT(DISTINCT word) as vocab FROM word_mastery")
            vocab_size = cursor.fetchone()["vocab"] or 0

            # 新词数（今日首次查询）
            cursor.execute(
                """
                SELECT COUNT(*) as new_words FROM word_mastery
                WHERE first_seen = ?
            """,
                (today,),
            )
            new_words = cursor.fetchone()["new_words"] or 0

            # 已掌握词汇
            cursor.execute("""
                SELECT COUNT(*) as mastered FROM word_mastery
                WHERE mastery_level >= 4 OR is_mastered = 1
            """)
            mastered_words = cursor.fetchone()["mastered"] or 0

            # 阅读时间
            cursor.execute(
                """
                SELECT SUM(duration_seconds) as total_time
                FROM reading_sessions
                WHERE DATE(start_time) = ?
            """,
                (today,),
            )
            total_time = cursor.fetchone()["total_time"] or 0

            # 下载论文数
            cursor.execute(
                """
                SELECT COUNT(*) as downloaded FROM papers
                WHERE DATE(download_date) = ?
            """,
                (today,),
            )
            papers_downloaded = cursor.fetchone()["downloaded"] or 0

            cursor.execute(
                """
                INSERT INTO daily_stats 
                (date, total_papers_read, total_words_queried, unique_words,
                 repeat_query_rate, avg_queries_per_paper, total_reading_time,
                 vocabulary_size, category_distribution, new_words, mastered_words, papers_downloaded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_papers_read = excluded.total_papers_read,
                    total_words_queried = excluded.total_words_queried,
                    unique_words = excluded.unique_words,
                    repeat_query_rate = excluded.repeat_query_rate,
                    avg_queries_per_paper = excluded.avg_queries_per_paper,
                    total_reading_time = excluded.total_reading_time,
                    vocabulary_size = excluded.vocabulary_size,
                    category_distribution = excluded.category_distribution,
                    new_words = excluded.new_words,
                    mastered_words = excluded.mastered_words,
                    papers_downloaded = excluded.papers_downloaded
            """,
                (
                    today,
                    today_data["papers"],
                    today_data["total_queries"],
                    today_data["unique_words"],
                    repeat_rate,
                    avg_queries,
                    total_time,
                    vocab_size,
                    json.dumps(category_dist),
                    new_words,
                    mastered_words,
                    papers_downloaded,
                ),
            )

            conn.commit()
            print(f"✓ 每日统计已更新: {today}")
        finally:
            conn.close()

    def query_stats(self, query_type, **params):
        """统计查询接口"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            result = {}

            if query_type == "word_frequency":
                days = params.get("days", 7)
                limit = params.get("limit", 20)
                cursor.execute(
                    """
                    SELECT word, COUNT(*) as count, SUM(query_count) as total
                    FROM word_queries
                    WHERE query_time >= DATE('now', '-{} days')
                    GROUP BY word
                    ORDER BY total DESC
                    LIMIT ?
                """.format(days),
                    (limit,),
                )
                result = {"words": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "learning_curve":
                days = params.get("days", 30)
                cursor.execute(
                    """
                    SELECT date, unique_words, vocabulary_size, 
                           total_words_queried, repeat_query_rate,
                           new_words, mastered_words
                    FROM daily_stats
                    WHERE date >= DATE('now', '-{} days')
                    ORDER BY date
                """.format(days)
                )
                result = {"daily_data": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "category_stats":
                cursor.execute("""
                    SELECT category, COUNT(DISTINCT paper_id) as papers,
                           COUNT(*) as queries, COUNT(DISTINCT word) as unique_words
                    FROM word_queries
                    WHERE category IS NOT NULL
                    GROUP BY category
                """)
                result = {"categories": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "mastery_distribution":
                cursor.execute("""
                    SELECT mastery_level, COUNT(*) as count
                    FROM word_mastery
                    GROUP BY mastery_level
                """)
                result = {"distribution": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "review_suggestions":
                cursor.execute(
                    """
                    SELECT word, query_count, first_seen, last_seen, review_count,
                           JULIANDAY('now') - JULIANDAY(last_seen) as days_since
                    FROM word_mastery
                    WHERE is_familiar = 0 AND review_count < 5
                    AND (JULIANDAY('now') - JULIANDAY(last_seen)) >= 
                        CASE review_count
                            WHEN 0 THEN 1
                            WHEN 1 THEN 2
                            WHEN 2 THEN 4
                            WHEN 3 THEN 7
                            WHEN 4 THEN 15
                        END
                    ORDER BY review_count DESC, days_since DESC
                    LIMIT ?
                """,
                    (params.get("limit", 20),),
                )
                result = {"suggestions": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "session_detail":
                session_id = params.get("session_id")
                cursor.execute(
                    "SELECT * FROM reading_sessions WHERE session_id = ?", (session_id,)
                )
                session = dict(cursor.fetchone()) if cursor.fetchone() else None
                if session:
                    cursor.execute(
                        """
                        SELECT word, translation, context, query_count
                        FROM word_queries
                        WHERE session_id = ?
                        ORDER BY query_time
                    """,
                        (session_id,),
                    )
                    session["words"] = [dict(row) for row in cursor.fetchall()]
                result = {"session": session}

            elif query_type == "word_history":
                word = params.get("word", "").lower()
                cursor.execute(
                    """
                    SELECT query_time, context, translation, paper_id, category
                    FROM word_queries
                    WHERE word = ?
                    ORDER BY query_time DESC
                """,
                    (word,),
                )
                result = {"history": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "reading_progress":
                # 阅读进度统计
                days = params.get("days", 30)
                cursor.execute(
                    """
                    SELECT 
                        COUNT(DISTINCT paper_id) as total_papers,
                        SUM(duration_seconds) / 3600.0 as total_hours,
                        AVG(duration_seconds) as avg_session_time,
                        SUM(pages_read) as total_pages
                    FROM reading_sessions
                    WHERE start_time >= DATE('now', '-{} days')
                """.format(days)
                )
                result = {"progress": dict(cursor.fetchone())}

            elif query_type == "vocabulary_growth":
                # 词汇增长趋势
                cursor.execute("""
                    SELECT 
                        DATE(first_seen) as date,
                        COUNT(*) as new_words
                    FROM word_mastery
                    WHERE first_seen >= DATE('now', '-30 days')
                    GROUP BY DATE(first_seen)
                    ORDER BY date
                """)
                result = {"growth": [dict(row) for row in cursor.fetchall()]}

            elif query_type == "difficult_words":
                # 难词统计（查询次数多但未掌握）
                limit = params.get("limit", 20)
                cursor.execute(
                    """
                    SELECT word, query_count, review_count,
                           JULIANDAY('now') - JULIANDAY(last_seen) as days_since
                    FROM word_mastery
                    WHERE is_familiar = 0 AND query_count >= 3
                    ORDER BY query_count DESC, days_since DESC
                    LIMIT ?
                """,
                    (limit,),
                )
                result = {"difficult_words": [dict(row) for row in cursor.fetchall()]}

            return result
        finally:
            conn.close()

    def reset_all_data(self, hard_reset=False):
        """重置所有用户数据"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # 保留论文元数据，只删除阅读记录
            cursor.execute("DELETE FROM word_queries")
            cursor.execute("DELETE FROM reading_sessions")
            cursor.execute("DELETE FROM daily_stats")
            cursor.execute("DELETE FROM word_mastery")
            cursor.execute("DELETE FROM familiar_words")

            if hard_reset:
                # 完全重置：删除所有论文数据
                cursor.execute("DELETE FROM papers")
            else:
                # 软重置：只重置阅读状态
                cursor.execute(
                    "UPDATE papers SET is_read = 0, read_count = 0, read_date = NULL,"
                    " last_read_time = NULL, query_count = 0, local_path = NULL"
                )
            conn.commit()
        finally:
            conn.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()
