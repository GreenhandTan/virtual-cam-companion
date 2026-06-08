"""
VirtualCam Companion - GUI 界面模块
基于 tkinter 的可视化界面
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from PIL import Image, ImageTk

from config import AppConfig
from cam_manager import VirtualCamManager
from api_server import APIServer, start_api_server
from utils import setup_logger, get_log_file

logger = setup_logger("GUI", get_log_file())


class VirtualCamApp:
    """虚拟摄像头 GUI 应用"""
    
    def __init__(self, config: AppConfig):
        """
        初始化 GUI 应用
        
        Args:
            config: 应用配置
        """
        self._config = config
        self._cam_manager = VirtualCamManager(
            width=config.cam_width,
            height=config.cam_height,
            fps=config.cam_fps
        )
        self._api_server: Optional[APIServer] = None
        self._current_image_path: Optional[str] = config.last_image
        self._photo_ref: Optional[ImageTk.PhotoImage] = None
        
        # 创建主窗口
        self._root = tk.Tk()
        self._root.title("📷 VirtualCam Companion")
        self._root.geometry(f"{config.window_width}x{config.window_height}")
        self._root.resizable(False, False)
        self._root.configure(bg="#1a1a2e")
        
        # 构建界面
        self._build_ui()
        
        # 启动 API 服务
        self._start_api()
        
        # 加载上次的图片
        if self._current_image_path and os.path.exists(self._current_image_path):
            self._load_image(self._current_image_path)
        
        # 注册关闭事件
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        """构建用户界面"""
        # 标题
        title = tk.Label(
            self._root, 
            text="📷 虚拟摄像头",
            font=("Segoe UI", 18, "bold"),
            fg="#fff", 
            bg="#1a1a2e"
        )
        title.pack(pady=(16, 8))
        
        # 状态标签
        self._status_var = tk.StringVar(value="⚠️ 未启动")
        self._status_label = tk.Label(
            self._root, 
            textvariable=self._status_var,
            font=("Segoe UI", 12),
            fg="#e8a0a0", 
            bg="#3d1f1f",
            padx=16, 
            pady=6
        )
        self._status_label.pack(pady=(0, 12))
        
        # 图片预览区域
        preview_frame = tk.Frame(
            self._root, 
            bg="#2a2a3e", 
            bd=0,
            highlightbackground="#444", 
            highlightthickness=1
        )
        preview_frame.pack(padx=24, pady=(0, 12))
        
        self._preview_label = tk.Label(
            preview_frame, 
            bg="#2a2a3e",
            text="点击下方按钮选择图片\n或拖拽图片到窗口",
            fg="#666", 
            font=("Segoe UI", 11),
            width=48, 
            height=12
        )
        self._preview_label.pack(padx=2, pady=2)
        
        # 图片信息标签
        self._info_var = tk.StringVar(value="")
        self._info_label = tk.Label(
            self._root, 
            textvariable=self._info_var,
            font=("Segoe UI", 10),
            fg="#999", 
            bg="#1a1a2e"
        )
        self._info_label.pack()
        
        # 按钮行
        btn_frame = tk.Frame(self._root, bg="#1a1a2e")
        btn_frame.pack(pady=12)
        
        style_btn = {
            "font": ("Segoe UI", 11, "bold"),
            "bd": 0, 
            "padx": 20, 
            "pady": 8, 
            "cursor": "hand2"
        }
        
        self._btn_select = tk.Button(
            btn_frame, 
            text="📁 选择图片",
            bg="#6c63ff", 
            fg="#fff",
            activebackground="#5a52d5",
            command=self._select_image, 
            **style_btn
        )
        self._btn_select.pack(side=tk.LEFT, padx=6)
        
        self._btn_start = tk.Button(
            btn_frame, 
            text="🚀 启动摄像头",
            bg="#2d6a4f", 
            fg="#fff",
            activebackground="#1b4332",
            command=self._toggle_camera, 
            **style_btn
        )
        self._btn_start.pack(side=tk.LEFT, padx=6)
        
        # API 信息
        api_frame = tk.Frame(self._root, bg="#1a1a2e")
        api_frame.pack(pady=(12, 4))
        
        api_label = tk.Label(
            api_frame,
            text=f"HTTP API: {self._config.api_address}",
            font=("Consolas", 9), 
            fg="#555", 
            bg="#1a1a2e"
        )
        api_label.pack()
        
        hint = tk.Label(
            api_frame,
            text="Chrome 扩展通过此 API 发送图片到虚拟摄像头",
            font=("Segoe UI", 9), 
            fg="#444", 
            bg="#1a1a2e"
        )
        hint.pack()
    
    def _start_api(self):
        """启动 API 服务"""
        self._api_server = start_api_server(self._cam_manager, self._config)
        if not self._api_server:
            logger.error("API 服务启动失败")
    
    def _select_image(self):
        """选择图片文件"""
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=self._config.get_file_types()
        )
        if path:
            self._load_image(path)
    
    def _load_image(self, path: str):
        """
        加载图片
        
        Args:
            path: 图片文件路径
        """
        if not os.path.exists(path):
            logger.warning(f"图片文件不存在: {path}")
            return
        
        self._current_image_path = path
        
        # 保存配置
        self._config.last_image = path
        self._config.save()
        
        # 加载到摄像头管理器
        self._cam_manager.set_image(path)
        
        # 显示预览
        try:
            img = Image.open(path)
            img.thumbnail((400, 280))
            self._photo_ref = ImageTk.PhotoImage(img)
            self._preview_label.configure(image=self._photo_ref, text="")
        except Exception as e:
            logger.error(f"预览图片失败: {e}")
            self._preview_label.configure(image="", text="预览失败")
        
        # 显示信息
        try:
            pil_img = Image.open(path)
            size_kb = os.path.getsize(path) / 1024
            self._info_var.set(
                f"{os.path.basename(path)}  {pil_img.width}×{pil_img.height}  {size_kb:.0f} KB"
            )
        except Exception:
            self._info_var.set(os.path.basename(path))
    
    def _toggle_camera(self):
        """切换摄像头状态"""
        if self._cam_manager.is_running:
            self._cam_manager.stop()
            self._status_var.set("⚠️ 已停止")
            self._status_label.configure(fg="#e8a0a0", bg="#3d1f1f")
            self._btn_start.configure(text="🚀 启动摄像头", bg="#2d6a4f")
        else:
            ok, msg = self._cam_manager.start()
            if ok:
                self._status_var.set(f"✅ {msg}")
                self._status_label.configure(fg="#95d5b2", bg="#1b4332")
                self._btn_start.configure(text="⏹ 停止", bg="#6a1a1a")
            else:
                messagebox.showerror("启动失败", msg)
    
    def _on_close(self):
        """窗口关闭处理"""
        logger.info("正在关闭应用...")
        
        # 停止摄像头
        self._cam_manager.stop()
        
        # 停止 API 服务
        if self._api_server:
            self._api_server.stop()
        
        # 销毁窗口
        self._root.destroy()
        logger.info("应用已关闭")
    
    def run(self):
        """运行应用主循环"""
        logger.info("应用启动")
        self._root.mainloop()
