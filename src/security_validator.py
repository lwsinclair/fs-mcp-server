"""
安全验证器：验证文件路径安全性
"""

import os
from pathlib import Path
from .config_manager import get_config_manager


class SecurityError(Exception):
    """安全验证错误"""
    pass


class FileSizeError(Exception):
    """文件大小错误"""
    pass


class SecurityValidator:
    """安全验证器"""
    
    def __init__(self):
        """初始化安全验证器"""
        current_config_manager = get_config_manager()
        self.safe_directory = current_config_manager.get_safe_directory()
        self.max_file_size_mb = current_config_manager.get_max_file_size_mb()
        self.allow_symlinks = current_config_manager.allow_symlinks()
    
    def get_safe_directory(self) -> str:
        """
        获取安全目录
        
        Returns:
            str: 安全目录路径
        """
        return self.safe_directory
    
    def validate_file_path(self, file_path) -> str:
        """
        验证文件路径的安全性
        
        Args:
            file_path: 文件路径（可以是相对路径或绝对路径）
            
        Returns:
            str: 验证后的绝对文件路径
            
        Raises:
            SecurityError: 路径不安全
            FileNotFoundError: 文件不存在
            FileSizeError: 文件过大
        """
        # 转换为绝对路径
        abs_file_path = os.path.abspath(os.path.expanduser(str(file_path)))
        
        # 检查文件是否存在
        if not os.path.exists(abs_file_path):
            raise FileNotFoundError(f"文件不存在: {abs_file_path}")
        
        # 检查是否为文件
        if not os.path.isfile(abs_file_path):
            raise SecurityError(f"路径不是文件: {abs_file_path}")
        
        # 检查符号链接
        if os.path.islink(abs_file_path) and not self.allow_symlinks:
            raise SecurityError(f"不允许访问符号链接: {abs_file_path}")
        
        # 检查文件是否在安全目录中
        if not self._is_file_in_safe_directory(abs_file_path):
            raise SecurityError(f"文件不在安全目录中: {abs_file_path}")
        
        # 检查文件大小
        try:
            file_size = os.path.getsize(abs_file_path)
            max_size_bytes = self.max_file_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                raise FileSizeError(f"文件过大: {file_size / (1024 * 1024):.1f}MB > {self.max_file_size_mb}MB")
        except OSError as e:
            raise SecurityError(f"无法获取文件大小: {e}")
        
        return abs_file_path
    
    def _is_file_in_safe_directory(self, abs_file_path: str) -> bool:
        """
        检查文件是否在安全目录中
        
        Args:
            abs_file_path: 文件的绝对路径
            
        Returns:
            bool: 是否在安全目录中
        """
        try:
            # 获取文件的绝对路径和安全目录的绝对路径
            file_path = Path(abs_file_path).resolve()
            safe_path = Path(self.safe_directory).resolve()
            
            # 检查文件路径是否以安全目录路径开始
            try:
                file_path.relative_to(safe_path)
                return True
            except ValueError:
                return False
                
        except Exception:
            return False
