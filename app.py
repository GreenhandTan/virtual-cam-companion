"""
VirtualCam Companion — 系统级虚拟摄像头
配合 Chrome 扩展使用，让任何网页都能检测到"摄像头设备"
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import base64
import json
import io
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    import pyvirtualcam
except ImportError:
    print("错误: pyvirtualcam 未安装。请运行: pip install pyvirtualcam opencv-python Pillow")
    sys.exit(1)


# ==================== 配置 ====================

API_PORT = 5566
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_image": None}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False)


# ==================== 虚拟摄像头核心 ====================

class VirtualCamManager:
    def __init__(self):
        self.cam = None
        self.running = False
        self.thread = None
        self.image = None          # 当前输出的图片 (numpy BGR)
        self.lock = threading.Lock()
        self.device_name = ""

    def set_image(self, image_path_or_array):
        """设置要输出的图片（文件路径或 numpy 数组）"""
        with self.lock:
            if isinstance(image_path_or_array, str):
                img = cv2.imread(image_path_or_array)
                if img is None:
                    return False
                self.image = img
            else:
                self.image = image_path_or_array
        return True

    def start(self, width=1280, height=720, fps=30):
        """启动虚拟摄像头"""
        if self.running:
            return True, "已在运行"

        # 确保有图片可输出
        with self.lock:
            if self.image is None:
                # 创建默认黑色占位画面
                self.image = np.zeros((height, width, 3), dtype=np.uint8)
                cv2.putText(self.image, "Virtual Camera", (width // 2 - 150, height // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (108, 99, 255), 2)

        try:
            self.cam = pyvirtualcam.Camera(width=width, height=height, fps=fps)
            self.device_name = self.cam.device
            self.running = True

            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

            return True, f"虚拟摄像头已启动: {self.device_name}"

        except Exception as e:
            return False, f"启动失败: {str(e)}\n\n请确认已安装虚拟摄像头驱动（OBS Virtual Camera）"

    def _loop(self):
        """持续输出帧"""
        fps = 30
        frame_duration = 1.0 / fps

        while self.running and self.cam:
            try:
                with self.lock:
                    img = self.image

                if img is not None:
                    # 调整尺寸匹配摄像头
                    frame = cv2.resize(img, (self.cam.width, self.cam.height))
                    # BGR -> RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.cam.send(frame)
                    self.cam.sleep_until_next_frame()
                else:
                    time.sleep(frame_duration)

            except Exception as e:
                print(f"[VirtualCam] 帧输出错误: {e}")
                time.sleep(0.1)

    def stop(self):
        """停止虚拟摄像头"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        if self.cam:
            try:
                self.cam.close()
            except Exception:
                pass
        self.cam = None
        self.device_name = ""

    @property
    def is_running(self):
        return self.running and self.cam is not None


# ==================== HTTP API（供 Chrome 扩展调用）====================

class APIHandler(BaseHTTPRequestHandler):
    cam_manager = None  # 由主程序设置

    def log_message(self, format, *args):
        pass  # 静默日志

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            mgr = self.cam_manager
            data = {
                "running": mgr.is_running if mgr else False,
                "device": mgr.device_name if mgr else "",
                "has_image": (mgr.image is not None) if mgr else False,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        elif self.path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b"pong")

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len else ""

        if self.path == "/api/set_image":
            try:
                data = json.loads(body)
                img_data = base64.b64decode(data["image"])
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img is not None:
                    self.cam_manager.set_image(img)
                    resp = {"ok": True}
                else:
                    resp = {"ok": False, "error": "图片解码失败"}

            except Exception as e:
                resp = {"ok": False, "error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        elif self.path == "/api/start":
            ok, msg = self.cam_manager.start()
            resp = {"ok": ok, "message": msg}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        elif self.path == "/api/stop":
            self.cam_manager.stop()
            resp = {"ok": True}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        else:
            self.send_response(404)
            self.end_headers()


def start_api_server(cam_manager):
    """启动 HTTP API 服务"""
    APIHandler.cam_manager = cam_manager
    server = HTTPServer(("127.0.0.1", API_PORT), APIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ==================== 主界面 ====================

class VirtualCamApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📷 VirtualCam Companion")
        self.root.geometry("480x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self.cam_manager = VirtualCamManager()
        self.config = load_config()
        self.current_image_path = self.config.get("last_image")
        self.photo_ref = None  # 防止 GC

        self._build_ui()
        self._start_api()

        # 加载上次的图片
        if self.current_image_path and os.path.exists(self.current_image_path):
            self._load_image(self.current_image_path)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # 标题
        title = tk.Label(self.root, text="📷 虚拟摄像头",
                         font=("Segoe UI", 18, "bold"),
                         fg="#fff", bg="#1a1a2e")
        title.pack(pady=(16, 8))

        # 状态
        self.status_var = tk.StringVar(value="⚠️ 未启动")
        self.status_label = tk.Label(self.root, textvariable=self.status_var,
                                      font=("Segoe UI", 12),
                                      fg="#e8a0a0", bg="#3d1f1f",
                                      padx=16, pady=6)
        self.status_label.pack(pady=(0, 12))

        # 图片预览区域
        preview_frame = tk.Frame(self.root, bg="#2a2a3e", bd=0,
                                  highlightbackground="#444", highlightthickness=1)
        preview_frame.pack(padx=24, pady=(0, 12))

        self.preview_label = tk.Label(preview_frame, bg="#2a2a3e",
                                       text="点击下方按钮选择图片\n或拖拽图片到窗口",
                                       fg="#666", font=("Segoe UI", 11),
                                       width=48, height=12)
        self.preview_label.pack(padx=2, pady=2)

        # 图片信息
        self.info_var = tk.StringVar(value="")
        self.info_label = tk.Label(self.root, textvariable=self.info_var,
                                    font=("Segoe UI", 10),
                                    fg="#999", bg="#1a1a2e")
        self.info_label.pack()

        # 按钮行
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=12)

        style_btn = {"font": ("Segoe UI", 11, "bold"),
                     "bd": 0, "padx": 20, "pady": 8, "cursor": "hand2"}

        self.btn_select = tk.Button(btn_frame, text="📁 选择图片",
                                     bg="#6c63ff", fg="#fff",
                                     activebackground="#5a52d5",
                                     command=self._select_image, **style_btn)
        self.btn_select.pack(side=tk.LEFT, padx=6)

        self.btn_start = tk.Button(btn_frame, text="🚀 启动摄像头",
                                    bg="#2d6a4f", fg="#fff",
                                    activebackground="#1b4332",
                                    command=self._toggle_camera, **style_btn)
        self.btn_start.pack(side=tk.LEFT, padx=6)

        # API 信息
        api_frame = tk.Frame(self.root, bg="#1a1a2e")
        api_frame.pack(pady=(12, 4))

        api_label = tk.Label(api_frame,
                              text=f"HTTP API: http://127.0.0.1:{API_PORT}",
                              font=("Consolas", 9), fg="#555", bg="#1a1a2e")
        api_label.pack()

        hint = tk.Label(api_frame,
                        text="Chrome 扩展通过此 API 发送图片到虚拟摄像头",
                        font=("Segoe UI", 9), fg="#444", bg="#1a1a2e")
        hint.pack()

    def _start_api(self):
        try:
            self.api_server = start_api_server(self.cam_manager)
            print(f"[VirtualCam] HTTP API 已启动: http://127.0.0.1:{API_PORT}")
        except Exception as e:
            print(f"[VirtualCam] API 启动失败: {e}")

    def _select_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self._load_image(path)

    def _load_image(self, path):
        if not os.path.exists(path):
            return

        self.current_image_path = path
        self.config["last_image"] = path
        save_config(self.config)

        # 加载到摄像头管理器
        self.cam_manager.set_image(path)

        # 显示预览
        try:
            img = Image.open(path)
            img.thumbnail((400, 280))
            self.photo_ref = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self.photo_ref, text="")
        except Exception:
            self.preview_label.configure(image="", text="预览失败")

        # 显示信息
        try:
            pil_img = Image.open(path)
            size_kb = os.path.getsize(path) / 1024
            self.info_var.set(f"{os.path.basename(path)}  {pil_img.width}×{pil_img.height}  {size_kb:.0f} KB")
        except Exception:
            self.info_var.set(os.path.basename(path))

    def _toggle_camera(self):
        if self.cam_manager.is_running:
            self.cam_manager.stop()
            self.status_var.set("⚠️ 已停止")
            self.status_label.configure(fg="#e8a0a0", bg="#3d1f1f")
            self.btn_start.configure(text="🚀 启动摄像头", bg="#2d6a4f")
        else:
            # 如果没有图片，用默认占位画面
            ok, msg = self.cam_manager.start()
            if ok:
                self.status_var.set(f"✅ {msg}")
                self.status_label.configure(fg="#95d5b2", bg="#1b4332")
                self.btn_start.configure(text="⏹ 停止", bg="#6a1a1a")
            else:
                messagebox.showerror("启动失败", msg)

    def _on_close(self):
        self.cam_manager.stop()
        if hasattr(self, "api_server"):
            self.api_server.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ==================== 入口 ====================

if __name__ == "__main__":
    app = VirtualCamApp()
    app.run()
