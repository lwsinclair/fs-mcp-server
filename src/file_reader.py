import os
from pathlib import Path
from typing import Union, Optional

from .security_validator import SecurityValidator, SecurityError, FileSizeError
from .file_converters import FileConverter
from .text_detector import get_text_detector
from .config_manager import get_config_manager


class UniversalFileReader:
    """通用文件读取器"""

    def __init__(self):
        """初始化文件读取器"""
        self.validator = SecurityValidator()
        current_config_manager = get_config_manager()
        # 从配置获取文档格式
        self.document_extensions = set(current_config_manager.get_document_extensions())
        self.default_encoding = current_config_manager.get_default_encoding()

    def read_file(
        self,
        file_path: Union[str, Path],
        start_line: int = 1,
        end_line: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径（相对路径或绝对路径）
            start_line: 开始行数（从1开始）
            end_line: 结束行数（包含，如果为None则读取到文件末尾）
            encoding: 文件编码，如果为None则自动检测或使用默认编码

        Returns:
            str: 文件内容

        Raises:
            SecurityError: 文件路径不安全
            FileNotFoundError: 文件不存在
            FileSizeError: 文件过大
            ValueError: 参数错误
            Exception: 文件读取或转换错误
        """
        # 验证路径安全性（自动转换为绝对路径）
        validated_path = self.validator.validate_file_path(file_path)

        # 验证行数参数
        if start_line < 1:
            raise ValueError("开始行数必须大于等于1")

        if end_line is not None and end_line < start_line:
            raise ValueError("结束行数不能小于开始行数")

        # 获取文件扩展名
        file_ext = Path(validated_path).suffix.lower()
        current_text_detector = get_text_detector()

        # 确定处理方式
        if file_ext in self.document_extensions:
            # 已知的文档格式，需要转换
            return self._read_document_file(validated_path, start_line, end_line)
        elif current_text_detector.is_text_file(validated_path):
            # 智能检测为文本文件
            actual_encoding = encoding or self._detect_encoding(validated_path)
            return self._read_text_file(validated_path, start_line, end_line, actual_encoding)
        else:
            # 不是文本文件也不是支持的文档格式
            raise ValueError(f"不支持的文件格式: {file_ext}，文件不是文本格式也不是支持的文档格式")

    def _detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 检测到的编码或默认编码
        """
        current_text_detector = get_text_detector()
        detected_encoding = current_text_detector.get_file_encoding(file_path)
        return detected_encoding or self.default_encoding

    def _read_text_file(
        self, file_path: str, start_line: int, end_line: Optional[int], encoding: str
    ) -> str:
        """
        读取纯文本文件

        Args:
            file_path: 文件路径
            start_line: 开始行数
            end_line: 结束行数
            encoding: 文件编码

        Returns:
            str: 文件内容
        """
        try:
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()

                # 计算实际的行范围
                total_lines = len(lines)
                start_idx = start_line - 1  # 转换为0索引
                end_idx = min(end_line, total_lines) if end_line else total_lines

                if start_idx >= total_lines:
                    return ""  # 开始行超出文件范围

                # 提取指定范围的行
                selected_lines = lines[start_idx:end_idx]
                return "".join(selected_lines)

        except UnicodeDecodeError as e:
            # 尝试自动检测编码
            if encoding != self.default_encoding:
                try:
                    return self._read_text_file(file_path, start_line, end_line, self.default_encoding)
                except UnicodeDecodeError:
                    pass
            raise Exception(f"文件编码错误，无法使用 {encoding} 编码读取: {e}")
        except Exception as e:
            raise Exception(f"文件读取失败: {e}")

    def _read_document_file(
        self, file_path: str, start_line: int, end_line: Optional[int]
    ) -> str:
        """
        读取文档文件（先转换为markdown再读取）

        Args:
            file_path: 文件路径
            start_line: 开始行数
            end_line: 结束行数

        Returns:
            str: 文件内容
        """
        file_ext = Path(file_path).suffix.lower()

        # 获取对应的转换器
        converter = FileConverter.get_converter_for_extension(file_ext)
        if not converter:
            raise ValueError(f"不支持的文档格式: {file_ext}")

        try:
            # 转换为markdown
            markdown_content = converter(file_path)

            # 分割成行并选择指定范围
            lines = markdown_content.split("\n")
            total_lines = len(lines)
            start_idx = start_line - 1  # 转换为0索引
            end_idx = min(end_line, total_lines) if end_line else total_lines

            if start_idx >= total_lines:
                return ""  # 开始行超出文件范围

            selected_lines = lines[start_idx:end_idx]
            return "\n".join(selected_lines)

        except Exception as e:
            raise Exception(f"文档文件处理失败: {e}")

    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 文件信息
        """
        validated_path = self.validator.validate_file_path(file_path)

        file_stat = os.stat(validated_path)
        file_ext = Path(validated_path).suffix.lower()
        
        current_text_detector = get_text_detector()
        # 使用智能检测判断文件类型
        detection_info = current_text_detector.get_detection_info(validated_path)
        is_text_file = detection_info['is_text']
        is_document_file = file_ext in self.document_extensions

        # 计算总行数
        total_lines = 0
        try:
            if is_document_file:
                converter = FileConverter.get_converter_for_extension(file_ext)
                if converter:
                    content = converter(validated_path)
                    total_lines = len(content.split("\n"))
            elif is_text_file:
                encoding = detection_info.get('encoding') or self.default_encoding
                with open(validated_path, "r", encoding=encoding) as file:
                    total_lines = sum(1 for _ in file)
        except Exception:
            total_lines = -1  # 无法计算行数

        return {
            "path": validated_path,
            "size": file_stat.st_size,
            "extension": file_ext,
            "total_lines": total_lines,
            "is_text_file": is_text_file,
            "is_document_file": is_document_file,
            "requires_conversion": is_document_file,
            "detected_encoding": detection_info.get('encoding'),
            "mime_type": detection_info.get('mime_type'),
            "file_type_detection": detection_info
        }

    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件格式是否受支持

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否支持该格式
        """
        try:
            current_text_detector = get_text_detector()
            # 如果文件存在，使用智能检测
            if os.path.exists(file_path):
                file_ext = Path(file_path).suffix.lower()
                return (file_ext in self.document_extensions or 
                       current_text_detector.is_text_file(file_path))
            else:
                # 如果文件不存在，只能根据扩展名判断
                file_ext = Path(file_path).suffix.lower()
                return file_ext in self.document_extensions
        except Exception:
            return False

    def get_supported_extensions(self) -> dict:
        """
        获取支持的文件扩展名信息
        
        Returns:
            dict: 支持的扩展名分类
        """
        current_config_manager = get_config_manager()
        return {
            "document_extensions": list(self.document_extensions),
            "binary_extensions": current_config_manager.get_binary_extensions(),
            "text_detection": "智能检测（不依赖扩展名）"
        }

    def get_safe_directory(self) -> str:
        """
        获取当前配置的安全目录
        
        Returns:
            str: 安全目录路径
        """
        return self.validator.get_safe_directory()


# 便利函数
def read_file(
    file_path: Union[str, Path],
    start_line: int = 1,
    end_line: Optional[int] = None,
    encoding: Optional[str] = None,
) -> str:
    """
    便利函数：读取文件内容

    Args:
        file_path: 文件路径
        start_line: 开始行数
        end_line: 结束行数
        encoding: 文件编码

    Returns:
        str: 文件内容
    """
    reader = UniversalFileReader()
    return reader.read_file(file_path, start_line, end_line, encoding)
