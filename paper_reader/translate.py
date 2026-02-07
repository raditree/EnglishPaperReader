"""
ECDICT 单文件翻译工具
功能：
1. 自动将 ecdict.csv 转换为轻量级 ecdict.db (SQLite)
2. 提供查询单词、模糊搜索等接口
"""

import sqlite3
import csv
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class ECDict:
    """ECDICT 词典工具类"""

    def __init__(self, csv_file: str = "ecdict.csv", db_file: str = "ecdict.db"):
        """
        初始化词典

        Args:
            csv_file: 词典源文件路径
            db_file: 生成的数据库路径
        """
        self.csv_file = Path(csv_file)
        self.db_file = Path(db_file)
        # 移除实例级别的连接，改用每次查询时创建新连接
        self.conn: Optional[sqlite3.Connection] = None

        # 确保数据库文件存在且可访问
        if not self.db_file.exists():
            print(f"警告: 数据库文件不存在 {self.db_file}")

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（单例模式）"""
        if self.conn is None:
            try:
                if not self.db_file.exists():
                    raise FileNotFoundError(
                        f"数据库文件不存在: {self.db_file}。请先调用 build_db() 方法构建数据库。"
                    )
                # 使用 check_same_thread=False 允许在不同线程中访问
                self.conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
                self.conn.row_factory = sqlite3.Row  # 返回字典格式
                # 设置超时时间
                self.conn.execute("PRAGMA timeout=30000")
                # 确保连接是可写的
                self.conn.execute("PRAGMA writable_schema=ON")
                # 设置默认的事务隔离级别
                self.conn.execute("PRAGMA journal_mode=WAL")
                # 设置默认的锁超时时间
                self.conn.execute("PRAGMA locking_mode=EXCLUSIVE")
                # 设置默认的同步模式
                self.conn.execute("PRAGMA synchronous=NORMAL")
                # 设置默认的缓存大小
                self.conn.execute("PRAGMA cache_size=1000")
                # 设置默认的页面大小
                self.conn.execute("PRAGMA page_size=4096")
                # 设置默认的最大内存使用量
                self.conn.execute("PRAGMA max_page_count=1000000")
                # 设置默认的自动真空
                self.conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
            except Exception as e:
                print(f"数据库连接错误: {e}")
                raise
        return self.conn

    def build_db(self, batch_size: int = 5000) -> None:
        """
        构建 SQLite 数据库

        Args:
            batch_size: 批量插入的行数，默认 5000
        """
        if not self.csv_file.exists():
            raise FileNotFoundError(f"找不到 CSV 文件: {self.csv_file}")

        print(f"正在构建数据库: {self.db_file}")
        print("这可能需要几分钟，请稍候...")

        # 1. 创建数据库连接
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()

        # 2. 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY,
                phonetic TEXT,
                definition TEXT,
                translation TEXT,
                pos TEXT,
                collins INTEGER,
                oxford INTEGER,
                tag TEXT,
                bnc INTEGER,
                frq INTEGER,
                exchange TEXT,
                detail TEXT,
                audio TEXT
            )
        ''')

        # 3. 创建索引（加快查询速度）
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans ON words(translation)')

        # 4. 读取 CSV 并导入
        # 注意：ecdict.csv 第一行是标题，需要跳过
        # 字段映射：word, phonetic, definition, translation, pos, collins, oxford, tag, bnc, frq, exchange, detail, audio

        print("开始导入数据...")

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行

            batch = []
            count = 0

            for row in reader:
                # 确保数据完整（至少前4列）
                if len(row) < 4:
                    continue

                # 补全数据到13列，防止报错
                data = row[:13] + [''] * (13 - len(row)) if len(row) < 13 else row[:13]

                batch.append(data)
                count += 1

                # 批量提交
                if len(batch) >= batch_size:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO words 
                        (word, phonetic, definition, translation, pos, collins, oxford, 
                         tag, bnc, frq, exchange, detail, audio)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch)
                    conn.commit()
                    print(f"已导入 {count} 条...", end='\r')
                    batch = []

            # 提交剩余数据
            if batch:
                cursor.executemany('''
                    INSERT OR REPLACE INTO words 
                    (word, phonetic, definition, translation, pos, collins, oxford, 
                     tag, bnc, frq, exchange, detail, audio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()

        conn.close()
        print(f"\n✓ 构建完成！共导入 {count} 个单词。")
        print(f"✓ 数据库大小: {self.db_file.stat().st_size / 1024 / 1024:.2f} MB")

    def is_built(self) -> bool:
        """检查数据库是否已构建"""
        return self.db_file.exists() and self.db_file.stat().st_size > 0

    def search(self, word: str) -> Optional[Dict[str, Any]]:
        """
        精确查询单词

        Args:
            word: 单词

        Returns:
            包含单词信息的字典，未找到返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM words 
            WHERE lower(word) = lower(?)
        ''', (word.strip(),))

        row = cursor.fetchone()
        return dict(row) if row else None

    def fuzzy_search(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        模糊搜索单词（前缀匹配）

        Args:
            keyword: 关键词
            limit: 返回数量

        Returns:
            单词列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT word, phonetic, translation, pos 
            FROM words 
            WHERE word LIKE ?
            ORDER BY bnc DESC
            LIMIT ?
        ''', (f"{keyword.lower()}%", limit))

        return [dict(row) for row in cursor.fetchall()]

    def search_by_chinese(self, chinese: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        中文反向查询

        Args:
            chinese: 中文释义
            limit: 返回数量

        Returns:
            单词列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT word, phonetic, translation, pos 
            FROM words 
            WHERE translation LIKE ?
            ORDER BY bnc DESC
            LIMIT ?
        ''', (f"%{chinese}%", limit))

        return [dict(row) for row in cursor.fetchall()]

    def run(self, user_input: str):
        if not user_input:
            return "未识别到单词"

        # 判断是否为中文
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_input)

        try:
            if is_chinese:
                # 中文反向查询
                results = self.search_by_chinese(user_input)
                if results:
                    # print(f"找到 {len(results)} 个结果:")
                    for item in results:
                        print(f"  • {item['word']} ({item['pos']}) - {item['translation']}")
                    return str(results)
                else:
                    return "未找到相关单词"
            else:
                # 英文精确查询
                result = self.search(user_input)
                if result:
                    # 如果有定义信息，也返回
                    definition = result.get('definition', '')
                    phonetic = result.get('phonetic', '')
                    translation = result.get('translation', '')

                    # 格式化输出
                    output = f"音标：/{phonetic or ''}/。释义：{translation}"
                    return output
                else:
                    # 如果精确匹配不到，尝试模糊搜索
                    print("未找到精确匹配，尝试模糊搜索...")
                    results = self.fuzzy_search(user_input)
                    if results:
                        for item in results:
                            print(f"  • {item['word']} - {item['translation']}")
                        return str(results)
                    else:
                        return "未找到该单词"
        except Exception as e:
            # 添加更详细的错误处理
            error_msg = f"[翻译错误] {str(e)}"
            print(f"翻译过程出错: {error_msg}")
            return error_msg

    def close(self):
        """关闭数据库连接"""
        # 不再需要关闭连接，因为每次查询都会创建新连接
        pass


# ==========================================
# 以下是命令行交互模式 (当直接运行此文件时)
# ==========================================
if __name__ == "__main__":
    # 配置文件名
    CSV_PATH = "ecdict.csv"
    DB_PATH = "ecdict.db"

    # 初始化工具
    tool = ECDict()# csv_file=CSV_PATH, db_file=DB_PATH)
    print(tool.run("million"))
"""
    # 1. 检查并构建数据库
    if not tool.is_built():
        print("未检测到数据库，开始从 ecdict.csv 构建...")
        try:
            tool.build_db()
        except Exception as e:
            print(f"构建失败: {e}")
            print("请确保 ecdict.csv 在当前目录下。")
            exit(1)
    else:
        print(f"数据库已就绪 ({DB_PATH})")

    # 2. 命令行交互
    print("\n" + "=" * 40)
    print("输入单词查询，输入 'q' 退出")
    print("=" * 40)

    while True:
        try:
            user_input = input("\n请输入: ").strip()

            if user_input.lower() in ['q', 'exit', 'quit']:
                break

            if not user_input:
                continue

            # 判断是否为中文
            is_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_input)

            if is_chinese:
                # 中文反向查询
                results = tool.search_by_chinese(user_input)
                if results:
                    print(f"找到 {len(results)} 个结果:")
                    for item in results:
                        print(f"  • {item['word']} ({item['pos']}) - {item['translation']}")
                else:
                    print("未找到相关单词")
            else:
                # 英文精确查询
                result = tool.search(user_input)
                if result:
                    print(f"\n【{result['word']}】{result['phonetic'] or ''}")
                    print(f"  释义: {result['translation']}")
                    if result['definition']:
                        print(f"  英文: {result['definition']}")
                    if result['collins']:
                        print(f"  星级: 柯林斯 {result['collins']} 星")
                else:
                    # 如果精确匹配不到，尝试模糊搜索
                    print("未找到精确匹配，尝试模糊搜索...")
                    results = tool.fuzzy_search(user_input)
                    if results:
                        for item in results:
                            print(f"  • {item['word']} - {item['translation']}")
                    else:
                        print("未找到该单词")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"发生错误: {e}")

    tool.close()
    print("再见！")
"""