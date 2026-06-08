"""
VirtualCam Companion — 系统级虚拟摄像头
配合 Chrome 扩展使用，让任何网页都能检测到"摄像头设备"

入口文件 - 程序启动点
"""

import sys
import os

# 确保当前目录在模块搜索路径中
if getattr(sys, 'frozen', False):
    # 打包后的 exe
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import AppConfig
from gui import VirtualCamApp
from utils import setup_logger, get_log_file


def main():
    """主函数"""
    # 初始化日志
    logger = setup_logger("Main", get_log_file())
    logger.info("=" * 50)
    logger.info("VirtualCam Companion 启动中...")
    
    # 检查依赖
    try:
        import pyvirtualcam
        logger.info(f"pyvirtualcam 版本: {pyvirtualcam.__version__}")
    except ImportError:
        logger.error("pyvirtualcam 未安装")
        print("错误: pyvirtualcam 未安装。请运行: pip install pyvirtualcam opencv-python Pillow")
        sys.exit(1)
    
    try:
        import cv2
        logger.info(f"OpenCV 版本: {cv2.__version__}")
    except ImportError:
        logger.error("opencv-python 未安装")
        print("错误: opencv-python 未安装。请运行: pip install opencv-python")
        sys.exit(1)
    
    try:
        from PIL import Image
        logger.info("Pillow 已安装")
    except ImportError:
        logger.error("Pillow 未安装")
        print("错误: Pillow 未安装。请运行: pip install Pillow")
        sys.exit(1)
    
    # 加载配置
    config = AppConfig.load()
    logger.info(f"配置加载完成: API 地址 {config.api_address}")
    
    # 启动应用
    try:
        app = VirtualCamApp(config)
        app.run()
    except Exception as e:
        logger.error(f"应用运行出错: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
