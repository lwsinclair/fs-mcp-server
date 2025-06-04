"""
配置管理器：使用.env文件管理配置
"""

import os
from typing import List, Any
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        load_dotenv()
    
    def get_safe_directory(self) -> str:
        """
        获取安全目录（只有一个）
        
        Returns:
            str: 安全目录的绝对路径
        """
        safe_dir = os.getenv("SAFE_DIRECTORY", ".")
        # 展开用户目录路径并转换为绝对路径
        expanded_path = os.path.expanduser(safe_dir.strip())
        abs_path = os.path.abspath(expanded_path)
        return abs_path
    
    def get_document_extensions(self) -> List[str]:
        """
        获取需要转换的文档格式列表
        
        Returns:
            List[str]: 文档扩展名列表
        """
        doc_exts_str = os.getenv("DOCUMENT_EXTENSIONS", ".docx,.xlsx,.xls,.pdf,.pptx,.odt,.ods")
        return [ext.strip() for ext in doc_exts_str.split(",") if ext.strip()]
    
    def get_binary_extensions(self) -> List[str]:
        """
        获取明确的二进制格式列表
        
        Returns:
            List[str]: 二进制文件扩展名列表
        """
        bin_exts_str = os.getenv("BINARY_EXTENSIONS", ".exe,.dll,.so,.dylib,.bin,.zip,.tar,.gz,.7z,.rar,.jpg,.jpeg,.png,.gif,.bmp,.ico,.mp3,.mp4,.avi,.mov,.wav")
        return [ext.strip() for ext in bin_exts_str.split(",") if ext.strip()]
    
    def get_default_encoding(self) -> str:
        """
        获取默认编码
        
        Returns:
            str: 默认编码
        """
        return os.getenv("DEFAULT_ENCODING", "utf-8")
    
    def get_max_file_size_mb(self) -> int:
        """
        获取最大文件大小限制（MB）
        
        Returns:
            int: 最大文件大小（MB）
        """
        return int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    
    def allow_symlinks(self) -> bool:
        """
        是否允许符号链接
        
        Returns:
            bool: 是否允许符号链接
        """
        return os.getenv("ALLOW_SYMLINKS", "false").lower() == "true"
    
    def get_text_detection_config(self) -> dict:
        """
        获取文本检测配置
        
        Returns:
            dict: 文本检测配置
        """
        return {
            "sample_bytes": int(os.getenv("TEXT_DETECTION_SAMPLE_BYTES", "8192")),
            "max_binary_ratio": float(os.getenv("TEXT_DETECTION_MAX_BINARY_RATIO", "0.1")),
            "use_mime_detection": os.getenv("TEXT_DETECTION_USE_MIME", "true").lower() == "true"
        }

# 单例实例存储
_config_manager_instance = None

def get_config_manager() -> ConfigManager:
    """
    获取ConfigManager的单例。
    在首次调用时创建实例。
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance 