# VirtualCam Companion

系统级虚拟摄像头工具，让 Windows 电脑出现一个"摄像头设备"，任何网页/软件都能检测到并使用。

## 工作原理

```
VirtualCam Companion (Python)
    │
    ▼
pyvirtualcam + OBS Virtual Camera 驱动
    │
    ▼
Windows 系统摄像头列表中出现 "OBS Virtual Camera"
    │
    ▼
浏览器 / Zoom / Teams 等软件自动识别为真实摄像头
```

## 安装（一键）

1. 确保已安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 Add to PATH）
2. 双击 `install.bat`
3. 等待安装完成

## 使用方法

### 独立使用

1. 双击 `run.bat` 或桌面快捷方式
2. 点击 **📁 选择图片** 加载要显示的画面
3. 点击 **🚀 启动摄像头**
4. 打开任意网页 → 请求摄像头时选择 "OBS Virtual Camera"
5. 网页看到的就是你选择的图片

### 配合 Chrome 扩展使用

1. 先启动本程序（后台运行，HTTP API 监听 `127.0.0.1:5566`）
2. 安装 Chrome 扩展
3. 在扩展中选择图片 → 自动发送到本程序
4. 本程序通过虚拟摄像头输出该图片

## 文件结构

```
virtual-cam-companion/
├── app.py              # 主程序（GUI + HTTP API）
├── requirements.txt    # Python 依赖
├── install.bat         # 一键安装脚本
├── run.bat             # 启动脚本
├── config.json         # 运行时配置（自动生成）
└── README.md           # 本文件
```

## HTTP API

本程序启动后会开启 HTTP 服务（端口 5566），供 Chrome 扩展调用：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ping` | GET | 检测程序是否运行 |
| `/api/status` | GET | 获取运行状态 |
| `/api/set_image` | POST | 发送图片（body: `{"image": "base64..."}`） |
| `/api/start` | POST | 启动虚拟摄像头 |
| `/api/stop` | POST | 停止虚拟摄像头 |

## 依赖

- Python 3.8+
- pyvirtualcam（提供 OBS Virtual Camera 驱动）
- opencv-python（图片处理）
- Pillow（图片预览）

## 常见问题

**Q: 提示"未检测到虚拟摄像头驱动"？**
A: pyvirtualcam 默认使用 OBS Virtual Camera 驱动。如果未自动注册，请安装 [OBS Studio](https://obsproject.com/)。

**Q: 浏览器中看不到虚拟摄像头？**
A: 确保先在本程序中点击"启动摄像头"，然后刷新网页。

**Q: 图片显示变形？**
A: 虚拟摄像头输出为 1280×720，图片会被拉伸适配。建议使用 16:9 比例的图片。
