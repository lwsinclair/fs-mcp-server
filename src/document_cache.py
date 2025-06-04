import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
logger = logging.getLogger(__name__)

# 缓存管理类
class DocumentCache:
    """文档转换缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保缓存已初始化"""
        if not self._initialized:
            self.cache_dir.mkdir(exist_ok=True)
            self.cache_index = self._load_cache_index()
            self._initialized = True
    
    def _load_cache_index(self) -> dict:
        """加载缓存索引"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存索引失败: {e}")
        return {}
    
    def _save_cache_index(self):
        """保存缓存索引"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存索引失败: {e}")
    
    def _get_file_md5(self, file_path: str) -> str:
        """计算文件MD5值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_cache_file_path(self, file_path: str) -> Path:
        """获取缓存文件路径"""
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.md"
    
    def get_cached_content(self, file_path: str) -> Optional[str]:
        """获取缓存的文档内容"""
        self._ensure_initialized()  # 延迟初始化
        
        abs_path = os.path.abspath(file_path)
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            return None
        
        # 检查缓存索引
        if abs_path not in self.cache_index:
            return None
        
        # 获取当前文件MD5
        current_md5 = self._get_file_md5(abs_path)
        cached_info = self.cache_index[abs_path]
        
        # 检查MD5是否匹配
        if cached_info.get('md5') != current_md5:
            logger.info(f"文件已更改，需要重新转换: {file_path}")
            return None
        
        # 读取缓存文件
        cache_file = self._get_cache_file_path(abs_path)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    logger.info(f"使用缓存文档: {file_path}")
                    return f.read()
            except Exception as e:
                logger.warning(f"读取缓存文件失败: {e}")
        
        return None
    
    def cache_content(self, file_path: str, content: str):
        """缓存文档内容"""
        self._ensure_initialized()  # 延迟初始化
        
        abs_path = os.path.abspath(file_path)
        
        try:
            # 计算文件MD5
            file_md5 = self._get_file_md5(abs_path)
            
            # 保存内容到缓存文件
            cache_file = self._get_cache_file_path(abs_path)
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新缓存索引
            self.cache_index[abs_path] = {
                'md5': file_md5,
                'cached_at': datetime.now().isoformat(),
                'cache_file': str(cache_file)
            }
            
            # 保存索引
            self._save_cache_index()
            logger.info(f"文档已缓存: {file_path}")
            
        except Exception as e:
            logger.error(f"缓存文档失败: {e}")