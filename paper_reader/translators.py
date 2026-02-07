"""翻译模块 - 处理单词翻译功能"""

import os
import sys
import translate
from batch_translator import get_batch_translator

# 全局批量翻译器实例
batch_translator = None


def get_global_batch_translator():
    """获取全局批量翻译器实例"""
    global batch_translator
    if batch_translator is None:
        # 查找词典数据库路径
        db_path = "ecdict.db"
        # 尝试在项目目录中查找
        for root, dirs, files in os.walk("."):
            if "ecdict.db" in files:
                db_path = os.path.join(root, "ecdict.db")
                break
        batch_translator = get_batch_translator(db_path)
    return batch_translator


def call_translator(word, context=""):
    """调用翻译接口（优先使用批量翻译器的缓存）"""
    try:
        if not word or not isinstance(word, str):
            return "[翻译错误] 无效的单词输入"

        translator = get_global_batch_translator()
        result = translator.translate(word.lower().strip())

        if result.translation.startswith("[翻译错误]"):
            return result.translation
        return result.translation
    except Exception as e:
        # 备用：使用原始翻译方式
        try:
            translate_tool = translate.ECDict()
            result = translate_tool.run(word)
            if isinstance(result, str) and result.startswith("[翻译错误]"):
                return result
            return result
        except Exception as e2:
            error_msg = f"[翻译错误] {str(e)}"
            print(f"翻译错误: {error_msg}")
            return error_msg
