import os
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document

from .text_detector import TextDetector
from .config_manager import get_config_manager
from .embedding_config import get_embedding_config, create_embeddings_client
from .progress_bar import ProgressBar, SimpleSpinner
from .file_converters import FileConverter
from .document_cache import DocumentCache

logger = logging.getLogger(__name__)

class VectorCodebaseIndexer:
    """基于向量嵌入的代码库索引器"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """初始化索引器"""
        self.config_manager = get_config_manager()
        self.safe_directory = self.config_manager.get_safe_directory()
        self.embedding_config = get_embedding_config()
        
        # 初始化文档缓存
        self.doc_cache = DocumentCache()
        
        # 设置向量数据库持久化目录
        if persist_directory is None:
            persist_directory = str(Path(self.safe_directory) / ".mcp_vectors")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 创建嵌入客户端
        self.embeddings = create_embeddings_client(self.embedding_config)
        
        # 初始化向量数据库
        self.vectorstore = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embeddings,
            collection_name="codebase_vectors"
        )
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.embedding_config.chunk_size,
            chunk_overlap=self.embedding_config.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # 段落分隔
                "\n",    # 行分隔
                " ",     # 词分隔
                "",      # 字符分隔
            ]
        )
        
        # 文本检测器
        self.text_detector = TextDetector()
        
        # 支持的文件扩展名
        self.supported_extensions = {
            # 代码文件
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.m', '.mm', '.pl', '.sh', '.bash', '.zsh', '.fish', '.ps1',
            
            # 配置和数据文件
            '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg', '.env',
            '.xml', '.html', '.htm', '.css', '.scss', '.sass', '.less',
            
            # 文档文件
            '.md', '.rst', '.txt', '.log', '.readme', '.changelog', '.license',
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            
            # 其他
            '.sql', '.dockerfile', '.makefile', '.gitignore', '.gitattributes'
        }
        
        # 排除的目录
        self.excluded_dirs = {
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.pytest_cache',
            '.venv', 'venv', 'env', '.env', 'build', 'dist', '.dist', 'target',
            '.idea', '.vscode', '.DS_Store', 'cache', '.cache', 'tmp', 'temp',
            '.mcp_index', '.mcp_vectors', 'logs'
        }
        
        # 最大文件大小 (10MB，支持较大的文档文件)
        self.max_file_size = 10 * 1024 * 1024
    
    def _get_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception:
            return ""
    
    def _should_index_file(self, file_path: Path) -> bool:
        """判断是否应该索引文件"""
        try:
            # 检查文件大小
            if file_path.stat().st_size > self.max_file_size:
                return False
            
            # 检查扩展名
            if file_path.suffix.lower() not in self.supported_extensions:
                # 检查是否为无扩展名的文本文件
                if file_path.suffix == '':
                    return self.text_detector.is_text_file(str(file_path))
                return False
            
            return True
            
        except Exception:
            return False
    
    def _should_skip_directory(self, dir_path: Path) -> bool:
        """判断是否应该跳过目录"""
        return dir_path.name in self.excluded_dirs or dir_path.name.startswith('.')
    
    def _extract_file_content(self, file_path: str) -> Tuple[str, Dict]:
        """提取文件内容和元数据"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # 检查是否是文档文件（需要转换）
            if file_ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']:
                # 尝试从缓存获取转换结果
                cached_content = self.doc_cache.get_cached_content(file_path)
                
                if cached_content is not None:
                    # 使用缓存内容
                    content = cached_content
                    logger.info(f"✅ 使用文档缓存: {Path(file_path).name}")
                else:
                    # 转换文档并缓存
                    converter = FileConverter.get_converter_for_extension(file_ext)
                    if converter is None:
                        logger.warning(f"不支持的文档格式: {file_ext}")
                        return "", {}
                    
                    try:
                        content = converter(file_path)
                        # 缓存转换结果
                        self.doc_cache.cache_content(file_path, content)
                        logger.info(f"🔄 文档转换并缓存: {Path(file_path).name}")
                    except Exception as e:
                        logger.warning(f"文档转换失败: {file_path}, 错误: {e}")
                        return "", {}
                
                encoding = 'utf-8'  # 转换后的内容都是UTF-8
            else:
                # 直接读取文本文件
                detected_info = self.text_detector.detect_file_info(file_path)
                encoding = detected_info.get('encoding', 'utf-8')
                
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
            
            # 获取文件信息
            file_stat = Path(file_path).stat()
            
            # 生成元数据
            metadata = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_ext': Path(file_path).suffix.lower(),
                'file_size': file_stat.st_size,
                'file_hash': self._get_file_hash(file_path),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'encoding': encoding,
                'content_length': len(content),
                'is_document_file': file_ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']
            }
            
            return content, metadata
            
        except Exception as e:
            logger.warning(f"无法读取文件内容: {file_path}, 错误: {e}")
            return "", {}
    
    def _scan_directory(self, directory: str) -> List[str]:
        """扫描目录并收集文件路径"""
        file_paths = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # 过滤排除的目录
                dirs[:] = [d for d in dirs if not self._should_skip_directory(Path(root) / d)]
                
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    if self._should_index_file(file_path):
                        file_paths.append(str(file_path.resolve()))
        
        except Exception as e:
            logger.error(f"扫描目录失败: {directory}, 错误: {e}")
        
        return file_paths
    
    def _create_documents_from_file(self, file_path: str) -> List[Document]:
        """从文件创建文档对象"""
        try:
            content, metadata = self._extract_file_content(file_path)
            
            if not content:
                return []
            
            # 计算相对路径
            try:
                relative_path = str(Path(file_path).relative_to(Path(self.safe_directory)))
            except ValueError:
                relative_path = str(Path(file_path).name)
            
            metadata['relative_path'] = relative_path
            
            # 分割文本
            chunks = self.text_splitter.split_text(content)
            
            # 创建文档对象
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': i,
                    'chunk_count': len(chunks),
                    'chunk_size': len(chunk)
                })
                
                doc = Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.warning(f"处理文件失败: {file_path}, 错误: {e}")
            return []
    
    async def index_files(self, file_paths: List[str]) -> Dict[str, int]:
        """索引文件列表"""
        indexed_files = 0
        indexed_chunks = 0
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 并行处理文件
            loop = asyncio.get_event_loop()
            tasks = []
            
            for file_path in file_paths:
                task = loop.run_in_executor(
                    executor,
                    self._create_documents_from_file,
                    file_path
                )
                tasks.append((file_path, task))
            
            # 收集所有文档
            all_documents = []
            
            for file_path, docs_task in tasks:
                try:
                    documents = await docs_task
                    
                    if documents:
                        # 检查是否需要更新（基于文件哈希）
                        file_hash = documents[0].metadata.get('file_hash', '')
                        
                        # 删除该文件的旧文档
                        existing_docs = self.vectorstore.get(
                            where={"file_path": file_path}
                        )
                        
                        if existing_docs['ids']:
                            # 检查是否需要更新
                            old_hash = None
                            if existing_docs['metadatas']:
                                old_hash = existing_docs['metadatas'][0].get('file_hash')
                            
                            if old_hash == file_hash:
                                continue  # 文件未更改，跳过
                            
                            # 删除旧文档
                            self.vectorstore.delete(ids=existing_docs['ids'])
                            logger.debug(f"删除旧文档: {file_path}")
                        
                        all_documents.extend(documents)
                        indexed_files += 1
                        indexed_chunks += len(documents)
                        
                        if indexed_files % 10 == 0:
                            logger.info(f"已处理 {indexed_files} 个文件...")
                
                except Exception as e:
                    logger.warning(f"索引文件失败: {file_path}, 错误: {e}")
                    continue
            
            # 批量添加到向量数据库
            if all_documents:
                logger.info(f"正在添加 {len(all_documents)} 个文档到向量数据库...")
                self.vectorstore.add_documents(all_documents)
                
                # 持久化（新版本已自动持久化）
                logger.info("向量数据库已持久化")
        
        return {
            'indexed_files': indexed_files,
            'indexed_chunks': indexed_chunks,
            'total_documents': len(all_documents)
        }
    
    async def rebuild_index(self, progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """重建整个索引"""
        start_time = datetime.now()
        logger.info(f"开始重建向量索引: {self.safe_directory}")
        
        try:
            # 创建进度指示器
            if progress_callback is None:
                spinner = SimpleSpinner("扫描代码库文件")
                def default_progress(stage, current=0, total=0, description=""):
                    if stage == "scanning":
                        spinner.update(description or "扫描文件中...")
                    elif stage == "scan_complete":
                        spinner.finish(f"扫描完成，发现 {total} 个文件")
                    elif stage == "indexing_start":
                        global progress_bar
                        progress_bar = ProgressBar(total, "索引文件")
                    elif stage == "indexing":
                        progress_bar.set_progress(current, description)
                    elif stage == "indexing_complete":
                        progress_bar.finish("索引完成")
                        
                progress_callback = default_progress
            
            # 扫描目录
            progress_callback("scanning")
            file_paths = await asyncio.get_event_loop().run_in_executor(
                None, self._scan_directory, self.safe_directory
            )
            progress_callback("scan_complete", total=len(file_paths))
            
            # 索引文件
            progress_callback("indexing_start", total=len(file_paths))
            result = await self._index_files_with_progress(file_paths, progress_callback)
            progress_callback("indexing_complete")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            final_result = {
                'scanned_files': len(file_paths),
                'indexed_files': result['indexed_files'],
                'indexed_chunks': result['indexed_chunks'],
                'total_documents': result['total_documents'],
                'duration_seconds': duration,
                'persist_directory': str(self.persist_directory)
            }
            
            logger.info(f"向量索引重建完成: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"重建向量索引失败: {e}")
            raise
    
    async def _index_files_with_progress(self, file_paths: List[str], progress_callback: Callable) -> Dict[str, int]:
        """带进度回调的文件索引"""
        indexed_files = 0
        indexed_chunks = 0
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 并行处理文件
            loop = asyncio.get_event_loop()
            tasks = []
            
            for file_path in file_paths:
                task = loop.run_in_executor(
                    executor,
                    self._create_documents_from_file,
                    file_path
                )
                tasks.append((file_path, task))
            
            # 收集所有文档
            all_documents = []
            
            for i, (file_path, docs_task) in enumerate(tasks):
                try:
                    documents = await docs_task
                    
                    if documents:
                        # 检查是否需要更新（基于文件哈希）
                        file_hash = documents[0].metadata.get('file_hash', '')
                        
                        # 删除该文件的旧文档
                        existing_docs = self.vectorstore.get(
                            where={"file_path": file_path}
                        )
                        
                        if existing_docs['ids']:
                            # 检查是否需要更新
                            old_hash = None
                            if existing_docs['metadatas']:
                                old_hash = existing_docs['metadatas'][0].get('file_hash')
                            
                            if old_hash == file_hash:
                                progress_callback("indexing", i + 1, description=f"跳过未变更文件: {Path(file_path).name}")
                                continue  # 文件未更改，跳过
                            
                            # 删除旧文档
                            self.vectorstore.delete(ids=existing_docs['ids'])
                            logger.debug(f"删除旧文档: {file_path}")
                        
                        all_documents.extend(documents)
                        indexed_files += 1
                        indexed_chunks += len(documents)
                        
                        progress_callback("indexing", i + 1, description=f"已处理: {Path(file_path).name}")
                    else:
                        progress_callback("indexing", i + 1, description=f"跳过空文件: {Path(file_path).name}")
                
                except Exception as e:
                    logger.warning(f"索引文件失败: {file_path}, 错误: {e}")
                    progress_callback("indexing", i + 1, description=f"处理失败: {Path(file_path).name}")
                    continue
            
            # 批量添加到向量数据库
            if all_documents:
                progress_callback("indexing", len(file_paths), description=f"正在保存 {len(all_documents)} 个文档...")
                self.vectorstore.add_documents(all_documents)
                
                # 持久化（新版本已自动持久化）
                logger.info("向量数据库已持久化")
        
        return {
            'indexed_files': indexed_files,
            'indexed_chunks': indexed_chunks,
            'total_documents': len(all_documents)
        }
    
    def get_index_stats(self) -> Dict[str, any]:
        """获取索引统计信息"""
        try:
            # 获取集合信息
            collection = self.vectorstore._collection
            collection_info = collection.get()
            
            total_docs = len(collection_info['ids']) if collection_info['ids'] else 0
            
            # 统计文件信息
            file_stats = {}
            if collection_info['metadatas']:
                file_paths = set()
                extensions = {}
                
                for metadata in collection_info['metadatas']:
                    if metadata:
                        file_path = metadata.get('file_path', '')
                        if file_path:
                            file_paths.add(file_path)
                        
                        file_ext = metadata.get('file_ext', '')
                        extensions[file_ext] = extensions.get(file_ext, 0) + 1
                
                file_stats = {
                    'unique_files': len(file_paths),
                    'extension_stats': extensions
                }
            
            return {
                'total_documents': total_docs,
                'total_files': file_stats.get('unique_files', 0),
                'extension_stats': file_stats.get('extension_stats', {}),
                'persist_directory': str(self.persist_directory),
                'embedding_model': self.embedding_config.model_name,
                'chunk_size': self.embedding_config.chunk_size
            }
            
        except Exception as e:
            logger.error(f"获取索引统计失败: {e}")
            return {
                'total_documents': 0,
                'total_files': 0,
                'extension_stats': {},
                'persist_directory': str(self.persist_directory),
                'embedding_model': self.embedding_config.model_name,
                'chunk_size': self.embedding_config.chunk_size,
                'error': str(e)
            }
    
    def clear_index(self):
        """清空索引"""
        try:
            # 获取所有文档ID
            collection = self.vectorstore._collection
            all_data = collection.get()
            
            if all_data['ids']:
                # 删除所有文档
                collection.delete(ids=all_data['ids'])
                logger.info("向量索引已清空")
            else:
                logger.info("索引已为空")
        except Exception as e:
            logger.error(f"清空索引失败: {e}")
            raise

# 保持向后兼容性
CodebaseIndexer = VectorCodebaseIndexer 