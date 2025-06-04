"""
智能文本检测器：判断文件是否为文本文件
"""

import os
import mimetypes
from pathlib import Path
from typing import Union, Optional, Dict, Any
import logging

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

from .config_manager import get_config_manager


class TextDetector:
    """智能文本检测器"""
    
    def __init__(self):
        """初始化文本检测器"""
        current_config_manager = get_config_manager()
        self.config = current_config_manager.get_text_detection_config()
        self.sample_bytes = self.config.get("sample_bytes", 8192)
        self.max_binary_ratio = self.config.get("max_binary_ratio", 0.1)
        self.use_mime_detection = self.config.get("use_mime_detection", True)
        
        # 已知的二进制扩展名
        self.binary_extensions = set(current_config_manager.get_binary_extensions())
        
        # 文本MIME类型
        self.text_mime_types = {
            'text/', 'application/json', 'application/xml', 'application/javascript',
            'application/x-sh', 'application/x-csh', 'application/x-python-code'
        }
    
    def is_text_file(self, file_path: Union[str, Path]) -> bool:
        """
        判断文件是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为文本文件
        """
        file_path = Path(file_path)
        
        # 1. 检查文件是否存在
        if not file_path.exists():
            return False
        
        # 2. 检查是否为目录
        if file_path.is_dir():
            return False
        
        # 3. 检查文件扩展名是否为明确的二进制格式
        file_ext = file_path.suffix.lower()
        if file_ext in self.binary_extensions:
            return False
        
        # 4. 检查文件大小（空文件视为文本文件）
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                return True
        except OSError:
            return False
        
        # 5. 使用MIME类型检测
        if self.use_mime_detection and self._is_text_by_mime(file_path):
            return True
        
        # 6. 使用文件内容检测
        return self._is_text_by_content(file_path)
    
    def _is_text_by_mime(self, file_path: Path) -> Optional[bool]:
        """
        通过MIME类型判断是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bool]: 如果能确定则返回bool，否则返回None
        """
        try:
            # 使用python-magic库（如果可用）
            if HAS_MAGIC:
                mime_type = magic.from_file(str(file_path), mime=True)
                return self._is_text_mime_type(mime_type)
            
            # 使用标准库的mimetypes
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type:
                return self._is_text_mime_type(mime_type)
        
        except Exception as e:
            logging.debug(f"MIME类型检测失败: {e}")
        
        return None
    
    def _is_text_mime_type(self, mime_type: str) -> bool:
        """
        判断MIME类型是否为文本类型
        
        Args:
            mime_type: MIME类型
            
        Returns:
            bool: 是否为文本类型
        """
        if not mime_type:
            return False
        
        mime_type = mime_type.lower()
        
        # 检查是否匹配文本MIME类型
        for text_mime in self.text_mime_types:
            if mime_type.startswith(text_mime):
                return True
        
        return False
    
    def _is_text_by_content(self, file_path: Path) -> bool:
        """
        通过文件内容判断是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为文本文件
        """
        try:
            with open(file_path, 'rb') as f:
                # 读取文件开头的一部分内容
                sample = f.read(self.sample_bytes)
                
                if not sample:
                    return True  # 空文件视为文本文件
                
                return self._analyze_bytes(sample)
        
        except (OSError, IOError) as e:
            logging.debug(f"读取文件内容失败: {e}")
            return False
    
    def _analyze_bytes(self, data: bytes) -> bool:
        """
        分析字节数据判断是否为文本
        
        Args:
            data: 字节数据
            
        Returns:
            bool: 是否为文本
        """
        if not data:
            return True
        
        # 检查是否包含NULL字节（强烈暗示为二进制文件）
        if b'\x00' in data:
            return False
        
        # 尝试用UTF-8解码
        try:
            text = data.decode('utf-8')
            # 成功解码，进一步检查内容
            return self._analyze_text_content(text)
        except UnicodeDecodeError:
            pass
        
        # 尝试其他常见编码
        for encoding in ['gbk', 'gb2312', 'latin1', 'cp1252']:
            try:
                text = data.decode(encoding)
                return self._analyze_text_content(text)
            except UnicodeDecodeError:
                continue
        
        # 如果都无法解码，分析字节特征
        return self._analyze_byte_patterns(data)
    
    def _analyze_text_content(self, text: str) -> bool:
        """
        分析文本内容特征
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否为文本
        """
        # 计算控制字符的比例
        control_chars = 0
        printable_chars = 0
        
        for char in text:
            if ord(char) < 32 and char not in '\t\r\n':
                control_chars += 1
            elif ord(char) >= 32 and ord(char) <= 126:
                printable_chars += 1
            elif ord(char) > 126:
                # Unicode字符，通常是文本
                printable_chars += 1
        
        total_chars = len(text)
        if total_chars == 0:
            return True
        
        # 如果控制字符比例过高，可能是二进制文件
        control_ratio = control_chars / total_chars
        return control_ratio <= self.max_binary_ratio
    
    def _analyze_byte_patterns(self, data: bytes) -> bool:
        """
        分析字节模式判断是否为文本
        
        Args:
            data: 字节数据
            
        Returns:
            bool: 是否为文本
        """
        # 计算各种字节的比例
        ascii_chars = 0
        high_bytes = 0
        
        for byte in data:
            if 32 <= byte <= 126:  # 可打印ASCII字符
                ascii_chars += 1
            elif byte >= 128:  # 高位字节
                high_bytes += 1
        
        total_bytes = len(data)
        if total_bytes == 0:
            return True
        
        # 如果大部分是可打印ASCII字符，可能是文本
        ascii_ratio = ascii_chars / total_bytes
        
        # 如果ASCII字符比例高，很可能是文本
        if ascii_ratio >= 0.7:
            return True
        
        # 如果高位字节很多但没有NULL字节，可能是UTF-8等编码的文本
        if high_bytes > 0 and ascii_ratio >= 0.3:
            return True
        
        return False
    
    def get_file_encoding(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        尝试检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的编码或None
        """
        file_path = Path(file_path)
        if not file_path.is_file():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(self.sample_bytes)
            
            if not sample:
                return None # 空文件无法判断编码
            
            # 尝试 UTF-8 (BOM or no BOM)
            try:
                sample.decode('utf-8-sig') # Handles UTF-8 BOM
                return 'utf-8-sig'
            except UnicodeDecodeError:
                try:
                    sample.decode('utf-8')
                    return 'utf-8'
                except UnicodeDecodeError:
                    pass # Not UTF-8
            
            # 尝试其他常见编码
            # TODO: 可以引入更强大的编码检测库如 chardet，但会增加依赖
            # 简单的启发式检测：
            common_encodings = ['gbk', 'gb2312', 'latin1', 'cp1252', 'iso-8859-1']
            for enc in common_encodings:
                try:
                    sample.decode(enc)
                    return enc
                except UnicodeDecodeError:
                    continue
            
            # 使用 python-magic (如果可用且能提供编码信息)
            if HAS_MAGIC:
                try:
                    mime_info = magic.from_file(str(file_path))
                    if 'charset=' in mime_info:
                        encoding = mime_info.split('charset=')[-1].split(';')[0].strip()
                        # python-magic 有时返回 binary，需要过滤
                        if encoding.lower() not in ['binary', 'unknown-8bit']:
                            return encoding.lower()
                except Exception:
                    pass # magic 库可能出错

        except (OSError, IOError):
            return None
        
        return None

    def get_detection_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取文件检测的详细信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            Dict[str, Any]: 检测信息字典
        """
        file_path_obj = Path(file_path)
        info = {
            'path': str(file_path_obj),
            'exists': file_path_obj.exists(),
            'is_file': file_path_obj.is_file(),
            'is_dir': file_path_obj.is_dir(),
            'size': None,
            'mime_type': None,
            'encoding': None,
            'is_text': None,
        }

        if not info['exists'] or not info['is_file']:
            info['is_text'] = False # 不存在或不是文件，则不是文本
            return info

        info['size'] = file_path_obj.stat().st_size

        # MIME Type
        if HAS_MAGIC:
            try:
                info['mime_type'] = magic.from_file(str(file_path_obj), mime=True)
            except Exception:
                pass # magic 库可能出错
        if not info['mime_type']:
            guessed_mime, _ = mimetypes.guess_type(str(file_path_obj))
            info['mime_type'] = guessed_mime

        # Encoding and Is Text
        info['encoding'] = self.get_file_encoding(file_path_obj)
        info['is_text'] = self.is_text_file(file_path_obj) # is_text_file 内部会做更全面的判断
        
        return info

# 单例实例存储
_text_detector_instance = None

def get_text_detector() -> TextDetector:
    """
    获取TextDetector的单例。
    在首次调用时创建实例。
    """
    global _text_detector_instance
    if _text_detector_instance is None:
        _text_detector_instance = TextDetector()
    return _text_detector_instance

# 移除旧的全局实例
# text_detector = TextDetector() 