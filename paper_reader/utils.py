"""工具函数和装饰器"""

import traceback
from functools import wraps
from flask import jsonify


def error_handler(f):
    """统一错误处理装饰器"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_info = traceback.format_exc()
            print(f"Error in {f.__name__}: {str(e)}")
            print(error_info)
            if isinstance(e, (ValueError, KeyError, TypeError)):
                return jsonify({"error": str(e), "code": 400}), 400
            else:
                return jsonify({"error": "Internal server error", "code": 500}), 500

    return wrapper
