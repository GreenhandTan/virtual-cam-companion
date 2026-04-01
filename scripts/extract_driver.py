"""
从 pyvirtualcam 包中提取 OBS 虚拟摄像头驱动 DLL
用于打包到安装包中
"""
import os
import shutil
import sys

def extract_driver(output_dir="driver"):
    try:
        import pyvirtualcam
        cam_dir = os.path.dirname(pyvirtualcam.__file__)
        
        # 查找 OBS 虚拟摄像头 DLL
        dll_path = os.path.join(cam_dir, "obs-virtualcam-module", "obs-virtualcam-module.dll")
        
        if not os.path.exists(dll_path):
            # 尝试其他可能的路径
            for root, dirs, files in os.walk(cam_dir):
                for f in files:
                    if "obs-virtualcam" in f.lower() and f.endswith(".dll"):
                        dll_path = os.path.join(root, f)
                        break
                if os.path.exists(dll_path):
                    break
        
        if os.path.exists(dll_path):
            os.makedirs(output_dir, exist_ok=True)
            dst = os.path.join(output_dir, "obs-virtualcam-module.dll")
            shutil.copy2(dll_path, dst)
            print(f"✅ 驱动已提取: {dst} ({os.path.getsize(dst) // 1024}KB)")
            return True
        else:
            print(f"❌ 未找到 OBS 虚拟摄像头驱动")
            print(f"   搜索路径: {cam_dir}")
            return False
            
    except ImportError:
        print("❌ pyvirtualcam 未安装")
        return False

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "driver"
    success = extract_driver(output)
    sys.exit(0 if success else 1)
