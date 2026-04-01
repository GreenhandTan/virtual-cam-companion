"""
从 pyvirtualcam 包中提取 OBS 虚拟摄像头驱动 DLL
兼容 pyvirtualcam 0.9.x (自带驱动)
"""
import os
import shutil
import sys

def extract_driver(output_dir="driver"):
    try:
        import pyvirtualcam
        cam_dir = os.path.dirname(pyvirtualcam.__file__)
        print(f"pyvirtualcam version: {pyvirtualcam.__version__}")
        print(f"pyvirtualcam dir: {cam_dir}")

        # 搜索所有 DLL 文件
        dll_candidates = []
        for root, dirs, files in os.walk(cam_dir):
            for f in files:
                if f.endswith(".dll"):
                    full = os.path.join(root, f)
                    dll_candidates.append(full)
                    print(f"  Found: {full} ({os.path.getsize(full) // 1024}KB)")

        # 优先找 obs-virtualcam 相关的 DLL
        vcam_dll = None
        for path in dll_candidates:
            basename = os.path.basename(path).lower()
            if "obs-virtualcam" in basename or "virtualcam" in basename:
                vcam_dll = path
                break

        # 如果没找到，用第一个 DLL（可能是 obs-virtualcam-module）
        if not vcam_dll and dll_candidates:
            vcam_dll = dll_candidates[0]

        if vcam_dll:
            os.makedirs(output_dir, exist_ok=True)
            dst = os.path.join(output_dir, "obs-virtualcam-module.dll")
            shutil.copy2(vcam_dll, dst)
            print(f"\n✅ 驱动已提取: {dst} ({os.path.getsize(dst) // 1024}KB)")
            return True
        else:
            print(f"\n❌ 未找到任何 DLL 文件")
            return False

    except ImportError:
        print("❌ pyvirtualcam 未安装")
        return False

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "driver"
    success = extract_driver(output)
    sys.exit(0 if success else 1)
