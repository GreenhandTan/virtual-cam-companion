"""
VirtualCam Companion - 工具模块
提供日志、验证等通用功能
"""

import logging
import os
import sys
from datetime import datetime


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    创建并配置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径 (可选)
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出 (可选)
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件 {log_file}: {e}")
    
    return logger


def validate_image_data(data: bytes, max_size_mb: int = 10) -> tuple[bool, str]:
    """
    验证图片数据是否有效
    
    Args:
        data: 图片二进制数据
        max_size_mb: 最大文件大小 (MB)
    
    Returns:
        (是否有效, 错误信息)
    """
    if not data:
        return False, "图片数据为空"
    
    # 检查大小限制
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"图片大小 {size_mb:.1f}MB 超过限制 {max_size_mb}MB"
    
    # 检查最小大小 (至少应该有一些数据)
    if len(data) < 100:
        return False, "图片数据过小，可能已损坏"
    
    return True, ""


def validate_base64_image(base64_str: str, max_size_mb: int = 10) -> tuple[bool, bytes, str]:
    """
    验证并解码 base64 图片数据
    
    Args:
        base64_str: base64 编码的图片字符串
        max_size_mb: 最大文件大小 (MB)
    
    Returns:
        (是否有效, 解码后的数据, 错误信息)
    """
    import base64
    
    if not base64_str:
        return False, b"", "图片数据为空"
    
    try:
        data = base64.b64decode(base64_str)
    except Exception as e:
        return False, b"", f"Base64 解码失败: {str(e)}"
    
    valid, error = validate_image_data(data, max_size_mb)
    if not valid:
        return False, b"", error
    
    return True, data, ""


def get_log_dir() -> str:
    """获取日志目录路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的 exe
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_log_file() -> str:
    """获取日志文件路径"""
    log_dir = get_log_dir()
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"virtualcam_{date_str}.log")
