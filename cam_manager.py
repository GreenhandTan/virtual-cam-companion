"""
VirtualCam Companion - 虚拟摄像头管理模块
负责虚拟摄像头的启动、停止、帧输出
"""

import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from utils import setup_logger, get_log_file

logger = setup_logger("VirtualCam", get_log_file())


class VirtualCamManager:
    """虚拟摄像头管理器"""
    
    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        """
        初始化摄像头管理器
        
        Args:
            width: 画面宽度
            height: 画面高度
            fps: 帧率
        """
        self._width = width
        self._height = height
        self._fps = fps
        
        self._cam = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._image: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._device_name = ""
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height
    
    @property
    def fps(self) -> int:
        return self._fps
    
    @property
    def device_name(self) -> str:
        return self._device_name
    
    @property
    def is_running(self) -> bool:
        return self._running and self._cam is not None
    
    @property
    def has_image(self) -> bool:
        return self._image is not None
    
    def set_image(self, image_path_or_array) -> bool:
        """
        设置要输出的图片
        
        Args:
            image_path_or_array: 文件路径 (str) 或 numpy 数组 (BGR)
        
        Returns:
            是否成功
        """
        with self._lock:
            if isinstance(image_path_or_array, str):
                img = cv2.imread(image_path_or_array)
                if img is None:
                    logger.error(f"无法读取图片: {image_path_or_array}")
                    return False
                self._image = img
                logger.info(f"已加载图片: {image_path_or_array}")
            elif isinstance(image_path_or_array, np.ndarray):
                self._image = image_path_or_array
                logger.info("已设置图片数据")
            else:
                logger.error(f"不支持的图片类型: {type(image_path_or_array)}")
                return False
        return True
    
    def start(self, width: int = None, height: int = None, fps: int = None) -> Tuple[bool, str]:
        """
        启动虚拟摄像头
        
        Args:
            width: 画面宽度 (None 使用默认值)
            height: 画面高度 (None 使用默认值)
            fps: 帧率 (None 使用默认值)
        
        Returns:
            (成功与否, 消息)
        """
        if self._running:
            return True, "已在运行"
        
        # 更新参数
        if width is not None:
            self._width = width
        if height is not None:
            self._height = height
        if fps is not None:
            self._fps = fps
        
        # 确保有图片可输出
        with self._lock:
            if self._image is None:
                self._create_placeholder()
        
        try:
            import pyvirtualcam
            self._cam = pyvirtualcam.Camera(
                width=self._width, 
                height=self._height, 
                fps=self._fps
            )
            self._device_name = self._cam.device
            self._running = True
            
            self._thread = threading.Thread(target=self._frame_loop, daemon=True)
            self._thread.start()
            
            msg = f"虚拟摄像头已启动: {self._device_name}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            err = str(e)
            logger.error(f"启动虚拟摄像头失败: {err}")
            
            if "No virtual camera" in err or "backend" in err.lower():
                return False, (
                    "未检测到虚拟摄像头驱动\n\n"
                    "请安装 OBS Studio（含 Virtual Camera）：\n"
                    "https://obsproject.com/\n\n"
                    "或运行以下命令安装驱动：\n"
                    "pip install pyvirtualcam\n"
                    "然后按提示操作"
                )
            return False, f"启动失败: {err}"
    
    def _create_placeholder(self):
        """创建默认占位画面"""
        self._image = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        text = "Virtual Camera"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (self._width - text_size[0]) // 2
        text_y = (self._height + text_size[1]) // 2
        cv2.putText(self._image, text, (text_x, text_y), font, font_scale, (108, 99, 255), thickness)
        logger.info("已创建默认占位画面")
    
    def _frame_loop(self):
        """帧输出循环"""
        frame_duration = 1.0 / self._fps
        
        while self._running and self._cam:
            try:
                with self._lock:
                    img = self._image
                
                if img is not None:
                    frame = cv2.resize(img, (self._cam.width, self._cam.height))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self._cam.send(frame)
                    self._cam.sleep_until_next_frame()
                else:
                    time.sleep(frame_duration)
                    
            except Exception as e:
                logger.error(f"帧输出错误: {e}")
                time.sleep(0.1)
    
    def stop(self):
        """停止虚拟摄像头"""
        if not self._running:
            return
        
        logger.info("正在停止虚拟摄像头...")
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        
        if self._cam:
            try:
                self._cam.close()
            except Exception as e:
                logger.warning(f"关闭摄像头时出错: {e}")
            self._cam = None
        
        self._device_name = ""
        logger.info("虚拟摄像头已停止")
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "running": self.is_running,
            "device": self._device_name,
            "has_image": self.has_image,
            "width": self._width,
            "height": self._height,
            "fps": self._fps
        }
