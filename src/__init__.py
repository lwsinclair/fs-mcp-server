"""
通用文件读取器包

支持读取多种文件格式：
- 文本文件：智能检测，不依赖文件扩展名
- 文档文件：docx, xlsx, pdf等（自动转换为markdown）

主要功能：
- .env配置文件驱动的安全目录管理
- 智能文本文件检测
- 按行范围读取文件内容
- 多格式文档转换
"""

from .file_reader import UniversalFileReader
from .document_cache import DocumentCache
from .file_converters import FileConverter
from .config_manager import get_config_manager
from .security_validator import SecurityValidator
from .text_detector import TextDetector

# 导入新的代码搜索模块
from .embedding_config import get_embedding_config, create_embeddings_client
from .codebase_indexer import VectorCodebaseIndexer, CodebaseIndexer
from .codebase_search import VectorCodebaseSearchEngine, CodebaseSearchEngine
from .index_scheduler import IndexScheduler
from .progress_bar import ProgressBar, SimpleSpinner

__version__ = "1.1.0"
__author__ = "Your Name"

__all__ = [
    # 原有模块
    'UniversalFileReader',
    'DocumentCache', 
    'FileConverter',
    'get_config_manager',
    'SecurityValidator',
    'TextDetector',
    
    # 新的代码搜索模块
    'get_embedding_config',
    'create_embeddings_client',
    'VectorCodebaseIndexer',
    'CodebaseIndexer',
    'VectorCodebaseSearchEngine',
    'CodebaseSearchEngine', 
    'IndexScheduler',
    'ProgressBar',
    'SimpleSpinner'
]
