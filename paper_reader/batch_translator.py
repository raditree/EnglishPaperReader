"""
批量翻译模块 - 优化论文阅读时的翻译体验
功能：
1. 从PDF文本中提取单词
2. 批量预翻译并缓存
3. 提供快速查询接口
"""

import re
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

import translate


@dataclass
class TranslationResult:
    """翻译结果数据类"""
    word: str
    translation: str
    phonetic: str = ""
    meaning: str = ""
    is_cached: bool = False
    query_time_ms: float = 0.0


class BatchTranslator:
    """批量翻译器 - 预加载和缓存论文中的单词翻译"""
    
    def __init__(self, db_path: str = "ecdict.db"):
        self.dict_path = db_path
        self._cache: Dict[str, TranslationResult] = {}
        self._lock = threading.RLock()
        self._translator: Optional[translate.ECDict] = None
        self._common_words: Set[str] = set()
        self._load_common_words()
        
    def _get_translator(self) -> translate.ECDict:
        """延迟初始化翻译器"""
        if self._translator is None:
            self._translator = translate.ECDict(db_file=self.dict_path)
        return self._translator
    
    def _load_common_words(self):
        """加载常见停用词（不需要翻译的词）"""
        # 常见停用词和短词
        self._common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'need', 'dare', 'ought', 'used', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
            'yours', 'hers', 'ours', 'theirs', 'myself', 'yourself', 'himself',
            'herself', 'itself', 'ourselves', 'yourselves', 'themselves',
            'what', 'which', 'who', 'whom', 'whose', 'whatever', 'whichever',
            'whoever', 'whomever', 'all', 'each', 'every', 'both', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how',
            'again', 'once', 'during', 'before', 'after', 'above', 'below',
            'up', 'down', 'out', 'off', 'over', 'under', 'further', 'on',
            'once', 'upon', 'am', 'pm', 'et', 'al', 'eg', 'ie', 'vs', 'etc',
            'fig', 'table', 'eq', 'sec', 'app', 'ref', 'no', 'nos', 'vol',
            'vols', 'ed', 'eds', 'pp', 'par', 'pars', 'chap', 'chaps'
        }
    
    def extract_words_from_text(self, text: str, min_length: int = 3) -> List[str]:
        """
        从文本中提取英文单词
        
        Args:
            text: 输入文本
            min_length: 最小单词长度
            
        Returns:
            去重后的单词列表
        """
        # 提取英文单词
        words = re.findall(r'[a-zA-Z]{%d,}' % min_length, text)
        
        # 转换为小写并去重
        unique_words = set()
        for word in words:
            word = word.lower().strip()
            # 过滤停用词和纯数字
            if word and word not in self._common_words and not word.isdigit():
                unique_words.add(word)
        
        return sorted(list(unique_words))
    
    def batch_translate(self, words: List[str], 
                        progress_callback=None) -> Dict[str, TranslationResult]:
        """
        批量翻译单词
        
        Args:
            words: 单词列表
            progress_callback: 进度回调函数 (current, total)
            
        Returns:
            单词到翻译结果的映射
        """
        results = {}
        total = len(words)
        
        # 首先检查缓存
        uncached_words = []
        with self._lock:
            for word in words:
                if word in self._cache:
                    results[word] = self._cache[word]
                else:
                    uncached_words.append(word)
        
        # 批量查询未缓存的单词
        if uncached_words:
            translator = self._get_translator()
            
            for i, word in enumerate(uncached_words):
                start_time = time.time()
                
                try:
                    dict_result = translator.search(word)
                    query_time = (time.time() - start_time) * 1000
                    
                    if dict_result:
                        phonetic = dict_result.get('phonetic', '')
                        translation = dict_result.get('translation', '')
                        definition = dict_result.get('definition', '')
                        
                        # 格式化翻译结果
                        if translation:
                            formatted = f"音标：/{phonetic}/。释义：{translation}"
                        elif definition:
                            formatted = f"释义：{definition}"
                        else:
                            formatted = "暂无翻译"
                        
                        result = TranslationResult(
                            word=word,
                            translation=formatted,
                            phonetic=phonetic,
                            meaning=translation or definition,
                            is_cached=False,
                            query_time_ms=query_time
                        )
                    else:
                        result = TranslationResult(
                            word=word,
                            translation=f"[未找到] {word}",
                            is_cached=False,
                            query_time_ms=query_time
                        )
                except Exception as e:
                    result = TranslationResult(
                        word=word,
                        translation=f"[翻译错误] {str(e)}",
                        is_cached=False,
                        query_time_ms=0
                    )
                
                results[word] = result
                
                # 存入缓存
                with self._lock:
                    self._cache[word] = result
                
                # 进度回调
                if progress_callback:
                    progress_callback(len(results), total)
        
        return results
    
    def translate(self, word: str) -> TranslationResult:
        """
        翻译单个单词（优先从缓存查询）
        
        Args:
            word: 要翻译的单词
            
        Returns:
            翻译结果
        """
        word = word.lower().strip()
        
        # 检查缓存
        with self._lock:
            if word in self._cache:
                cached = self._cache[word]
                return TranslationResult(
                    word=cached.word,
                    translation=cached.translation,
                    phonetic=cached.phonetic,
                    meaning=cached.meaning,
                    is_cached=True,
                    query_time_ms=0
                )
        
        # 缓存未命中，查询词典
        start_time = time.time()
        
        try:
            translator = self._get_translator()
            dict_result = translator.search(word)
            query_time = (time.time() - start_time) * 1000
            
            if dict_result:
                phonetic = dict_result.get('phonetic', '')
                translation = dict_result.get('translation', '')
                definition = dict_result.get('definition', '')
                
                if translation:
                    formatted = f"音标：/{phonetic}/。释义：{translation}"
                elif definition:
                    formatted = f"释义：{definition}"
                else:
                    formatted = "暂无翻译"
                
                result = TranslationResult(
                    word=word,
                    translation=formatted,
                    phonetic=phonetic,
                    meaning=translation or definition,
                    is_cached=False,
                    query_time_ms=query_time
                )
            else:
                result = TranslationResult(
                    word=word,
                    translation=f"[未找到] {word}",
                    is_cached=False,
                    query_time_ms=query_time
                )
            
            # 存入缓存
            with self._lock:
                self._cache[word] = result
            
            return result
            
        except Exception as e:
            return TranslationResult(
                word=word,
                translation=f"[翻译错误] {str(e)}",
                is_cached=False,
                query_time_ms=0
            )
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'cached_words': list(self._cache.keys())[:100]  # 最多返回100个
            }
    
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def preload_paper_words(self, text_content: str, 
                           progress_callback=None) -> Dict[str, TranslationResult]:
        """
        预加载论文中的所有单词
        
        Args:
            text_content: PDF文本内容
            progress_callback: 进度回调
            
        Returns:
            翻译结果字典
        """
        # 提取单词
        words = self.extract_words_from_text(text_content)
        
        # 批量翻译
        return self.batch_translate(words, progress_callback)


# 全局批量翻译器实例
_batch_translator: Optional[BatchTranslator] = None
_translator_lock = threading.Lock()


def get_batch_translator(db_path: str = "ecdict.db") -> BatchTranslator:
    """获取全局批量翻译器实例（单例模式）"""
    global _batch_translator
    
    with _translator_lock:
        if _batch_translator is None:
            _batch_translator = BatchTranslator(db_path)
        return _batch_translator


def reset_batch_translator():
    """重置全局翻译器实例"""
    global _batch_translator
    
    with _translator_lock:
        _batch_translator = None


# 兼容性函数，保持与原有translate.py的接口一致
def call_translator(word: str, context: str = '', db_path: str = "ecdict.db") -> str:
    """
    调用翻译接口（兼容旧接口）
    
    Args:
        word: 要翻译的单词
        context: 上下文（保留参数，暂未使用）
        db_path: 词典数据库路径
        
    Returns:
        翻译结果字符串
    """
    translator = get_batch_translator(db_path)
    result = translator.translate(word)
    return result.translation


if __name__ == "__main__":
    # 测试代码
    bt = BatchTranslator()
    
    # 测试文本
    test_text = """
    Deep learning has revolutionized computer vision and natural language processing.
    Neural networks with multiple layers can learn hierarchical representations of data.
    Convolutional neural networks are particularly effective for image classification tasks.
    """
    
    print("提取的单词:")
    words = bt.extract_words_from_text(test_text)
    for w in words[:10]:
        print(f"  - {w}")
    
    print(f"\n共提取 {len(words)} 个单词")
    
    # 测试批量翻译
    print("\n批量翻译前5个单词:")
    results = bt.batch_translate(words[:5], 
                                  progress_callback=lambda c, t: print(f"  进度: {c}/{t}"))
    
    for word, result in results.items():
        cached_status = "[缓存]" if result.is_cached else "[新查]"
        print(f"  {cached_status} {word}: {result.translation[:50]}...")
    
    # 测试缓存命中
    print("\n再次查询（测试缓存）:")
    result = bt.translate(words[0])
    print(f"  {'[缓存]' if result.is_cached else '[新查]'} {result.word}: {result.translation[:50]}...")
