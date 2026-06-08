"""
VirtualCam Companion - 配置管理模块
支持配置文件加载、保存、默认值
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class AppConfig:
    """应用配置类"""
    
    # API 配置
    api_host: str = "127.0.0.1"
    api_port: int = 5566
    
    # 摄像头配置
    cam_width: int = 1280
    cam_height: int = 720
    cam_fps: int = 30
    
    # 图片配置
    max_image_size_mb: int = 10
    supported_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "bmp", "webp"])
    
    # 用户配置
    last_image: Optional[str] = None
    
    # GUI 配置
    window_width: int = 480
    window_height: int = 560
    theme: str = "dark"  # dark/light
    
    @classmethod
    def get_config_path(cls) -> str:
        """获取配置文件路径"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "config.json")
    
    @classmethod
    def load(cls, config_path: str = None) -> 'AppConfig':
        """
        从文件加载配置，缺失项使用默认值
        
        Args:
            config_path: 配置文件路径，None 则使用默认路径
        
        Returns:
            AppConfig 实例
        """
        if config_path is None:
            config_path = cls.get_config_path()
        
        config = cls()
        
        if not os.path.exists(config_path):
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 只更新存在的字段，忽略未知字段
            valid_fields = {k for k in cls.__dataclass_fields__}
            for key, value in data.items():
                if key in valid_fields:
                    setattr(config, key, value)
                    
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
        except Exception as e:
            print(f"配置加载失败: {e}")
        
        return config
    
    def save(self, config_path: str = None):
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，None 则使用默认路径
        """
        if config_path is None:
            config_path = self.get_config_path()
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"配置保存失败: {e}")
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的图片扩展名列表 (带点号)"""
        return [f".{ext}" for ext in self.supported_formats]
    
    def get_file_types(self) -> list:
        """获取文件选择器的文件类型过滤器"""
        exts = " ".join(f"*.{ext}" for ext in self.supported_formats)
        return [("图片文件", exts), ("所有文件", "*.*")]
    
    @property
    def api_address(self) -> str:
        """获取 API 完整地址"""
        return f"http://{self.api_host}:{self.api_port}"


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = AppConfig.load()
    return _config
