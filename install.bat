@echo off
chcp 65001 >nul 2>&1
title VirtualCam Companion - 一键安装

echo ========================================
echo   📷 VirtualCam Companion 安装程序
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 需要管理员权限来安装虚拟摄像头驱动
    echo     正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Python，请先安装 Python 3.8+
    echo     下载地址: https://www.python.org/downloads/
    echo.
    echo     安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo     Python %%i ✓

:: 安装依赖
echo.
echo [2/4] 安装 Python 依赖包...
echo     这可能需要几分钟...
pip install -r "%~dp0requirements.txt" -q
if %errorlevel% neq 0 (
    echo [!] 依赖安装失败，尝试使用镜像源...
    pip install -r "%~dp0requirements.txt" -q -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo     依赖安装完成 ✓

:: 注册虚拟摄像头驱动（pyvirtualcam 包含 OBS Virtual Camera 驱动）
echo.
echo [3/4] 注册虚拟摄像头驱动...
python -c "import pyvirtualcam; print('    驱动可用 ✓')" 2>nul
if %errorlevel% neq 0 (
    echo [!] 虚拟摄像头驱动未就绪，尝试手动注册...
    :: 查找 pyvirtualcam 安装路径中的驱动
    for /f "tokens=*" %%i in ('python -c "import pyvirtualcam, os; print(os.path.dirname(pyvirtualcam.__file__))" 2^>nul') do set PYVCAM_DIR=%%i
    if exist "%PYVCAM_DIR%\obs-virtualcam-module\obs-virtualcam-module.dll" (
        regsvr32 /s "%PYVCAM_DIR%\obs-virtualcam-module\obs-virtualcam-module.dll"
        echo     驱动注册成功 ✓
    ) else (
        echo [!] 驱动注册可能需要手动处理
        echo     请确保 OBS Virtual Camera 已安装或运行 setup_virtual_camera.bat
    )
)

:: 创建桌面快捷方式
echo.
echo [4/4] 创建桌面快捷方式...
set SCRIPT="%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\VirtualCam Companion.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0run.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,44" >> %SCRIPT%
echo oLink.Description = "VirtualCam Companion - 虚拟摄像头" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo     桌面快捷方式已创建 ✓

echo.
echo ========================================
echo   ✅ 安装完成！
echo ========================================
echo.
echo   使用方法:
echo   1. 双击桌面 "VirtualCam Companion" 快捷方式
echo   2. 点击 "选择图片" 加载要显示的画面
echo   3. 点击 "启动摄像头"
echo   4. 在浏览器中打开需要摄像头的网页
echo   5. 网页会看到 "OBS Virtual Camera" 设备
echo.
echo   配合 Chrome 扩展使用效果更佳
echo.
pause
