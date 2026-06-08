"""
VirtualCam Companion - HTTP API 服务模块
提供 REST API 供 Chrome 扩展调用
包含完整的输入验证和错误处理
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import cv2
import numpy as np

from config import AppConfig
from cam_manager import VirtualCamManager
from utils import setup_logger, get_log_file, validate_base64_image

logger = setup_logger("APIServer", get_log_file())

# 请求体大小限制 (10MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024


class APIHandler(BaseHTTPRequestHandler):
    """HTTP API 请求处理器"""
    
    cam_manager: Optional[VirtualCamManager] = None
    config: Optional[AppConfig] = None
    
    def log_message(self, format, *args):
        """重写日志方法，使用统一日志"""
        logger.debug(f"{self.client_address[0]} - {format % args}")
    
    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_error(self, message: str, status: int = 400, error_code: str = None):
        """发送错误响应"""
        resp = {"ok": False, "error": message}
        if error_code:
            resp["error_code"] = error_code
        self._send_json(resp, status)
    
    def _cors_headers(self):
        """添加 CORS 头"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def _read_body(self) -> Optional[str]:
        """
        读取请求体，包含大小验证
        
        Returns:
            请求体字符串，失败返回 None
        """
        content_length = self.headers.get("Content-Length")
        
        if not content_length:
            return ""
        
        try:
            content_length = int(content_length)
        except ValueError:
            self._send_error("无效的 Content-Length", 400, "INVALID_CONTENT_LENGTH")
            return None
        
        # 检查大小限制
        if content_length > MAX_REQUEST_SIZE:
            self._send_error(
                f"请求体过大: {content_length / 1024 / 1024:.1f}MB，限制 {MAX_REQUEST_SIZE / 1024 / 1024}MB",
                413,
                "REQUEST_TOO_LARGE"
            )
            return None
        
        try:
            body = self.rfile.read(content_length)
            return body.decode('utf-8')
        except Exception as e:
            logger.error(f"读取请求体失败: {e}")
            self._send_error("读取请求体失败", 500, "READ_BODY_ERROR")
            return None
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/api/ping":
            self._handle_ping()
        elif self.path == "/api/status":
            self._handle_status()
        else:
            self._send_error(f"未找到接口: {self.path}", 404, "NOT_FOUND")
    
    def do_POST(self):
        """处理 POST 请求"""
        body = self._read_body()
        if body is None:
            return  # 已经发送了错误响应
        
        if self.path == "/api/set_image":
            self._handle_set_image(body)
        elif self.path == "/api/start":
            self._handle_start()
        elif self.path == "/api/stop":
            self._handle_stop()
        else:
            self._send_error(f"未找到接口: {self.path}", 404, "NOT_FOUND")
    
    # ==================== 具体处理方法 ====================
    
    def _handle_ping(self):
        """处理 ping 请求"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(b"pong")
    
    def _handle_status(self):
        """处理状态查询请求"""
        if not self.cam_manager:
            self._send_json({"running": False, "device": "", "has_image": False})
            return
        
        status = self.cam_manager.get_status()
        self._send_json(status)
    
    def _handle_set_image(self, body: str):
        """
        处理设置图片请求
        
        请求格式: {"image": "base64编码的图片数据"}
        """
        # 1. 解析 JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
            self._send_error(f"JSON 格式错误: {str(e)}", 400, "INVALID_JSON")
            return
        
        # 2. 验证字段存在
        if "image" not in data:
            self._send_error("缺少 'image' 字段", 400, "MISSING_FIELD")
            return
        
        # 3. 验证字段类型
        if not isinstance(data["image"], str):
            self._send_error("'image' 字段必须是字符串", 400, "INVALID_FIELD_TYPE")
            return
        
        # 4. 验证并解码 base64
        max_size = self.config.max_image_size_mb if self.config else 10
        valid, img_data, error = validate_base64_image(data["image"], max_size)
        if not valid:
            logger.warning(f"图片验证失败: {error}")
            self._send_error(error, 400, "INVALID_IMAGE_DATA")
            return
        
        # 5. 解码图片
        try:
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                self._send_error("图片解码失败，不支持的格式", 400, "IMAGE_DECODE_FAILED")
                return
            
            # 6. 设置到摄像头管理器
            if not self.cam_manager:
                self._send_error("摄像头管理器未初始化", 500, "CAM_NOT_INITIALIZED")
                return
            
            success = self.cam_manager.set_image(img)
            if success:
                logger.info(f"已接收图片: {img.shape[1]}x{img.shape[0]}")
                self._send_json({"ok": True})
            else:
                self._send_error("设置图片失败", 500, "SET_IMAGE_FAILED")
                
        except Exception as e:
            logger.error(f"处理图片时出错: {e}")
            self._send_error(f"处理图片时出错: {str(e)}", 500, "IMAGE_PROCESS_ERROR")
    
    def _handle_start(self):
        """处理启动摄像头请求"""
        if not self.cam_manager:
            self._send_error("摄像头管理器未初始化", 500, "CAM_NOT_INITIALIZED")
            return
        
        ok, msg = self.cam_manager.start()
        self._send_json({"ok": ok, "message": msg})
    
    def _handle_stop(self):
        """处理停止摄像头请求"""
        if not self.cam_manager:
            self._send_error("摄像头管理器未初始化", 500, "CAM_NOT_INITIALIZED")
            return
        
        self.cam_manager.stop()
        self._send_json({"ok": True, "message": "已停止"})


class APIServer:
    """API 服务器封装"""
    
    def __init__(self, cam_manager: VirtualCamManager, config: AppConfig):
        """
        初始化 API 服务器
        
        Args:
            cam_manager: 摄像头管理器实例
            config: 应用配置
        """
        self._cam_manager = cam_manager
        self._config = config
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    @property
    def is_running(self) -> bool:
        return self._server is not None
    
    @property
    def address(self) -> str:
        return f"http://{self._config.api_host}:{self._config.api_port}"
    
    def start(self) -> bool:
        """
        启动 API 服务器
        
        Returns:
            是否成功启动
        """
        if self._server:
            logger.warning("API 服务器已在运行")
            return True
        
        try:
            # 设置处理器的类变量
            APIHandler.cam_manager = self._cam_manager
            APIHandler.config = self._config
            
            self._server = HTTPServer(
                (self._config.api_host, self._config.api_port),
                APIHandler
            )
            
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            
            logger.info(f"HTTP API 已启动: {self.address}")
            return True
            
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error(f"端口 {self._config.api_port} 已被占用")
            else:
                logger.error(f"启动 API 服务器失败: {e}")
            self._server = None
            return False
        except Exception as e:
            logger.error(f"启动 API 服务器失败: {e}")
            self._server = None
            return False
    
    def stop(self):
        """停止 API 服务器"""
        if not self._server:
            return
        
        logger.info("正在停止 API 服务器...")
        self._server.shutdown()
        self._server = None
        self._thread = None
        logger.info("API 服务器已停止")


def start_api_server(cam_manager: VirtualCamManager, config: AppConfig) -> Optional[APIServer]:
    """
    启动 API 服务器的便捷函数
    
    Args:
        cam_manager: 摄像头管理器
        config: 应用配置
    
    Returns:
        APIServer 实例，失败返回 None
    """
    server = APIServer(cam_manager, config)
    if server.start():
        return server
    return None
