import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
import logging

from langchain.schema import Document

from .codebase_indexer import VectorCodebaseIndexer

logger = logging.getLogger(__name__)

class VectorCodebaseSearchEngine:
    """基于向量相似性的代码库搜索引擎"""
    
    def __init__(self, indexer: Optional[VectorCodebaseIndexer] = None):
        """初始化搜索引擎"""
        self.indexer = indexer or VectorCodebaseIndexer()
        self.vectorstore = self.indexer.vectorstore
    
    async def semantic_search(
        self,
        query: str,
        k: int = 30,
        score_threshold: float = 0.0,
        file_extensions: Optional[List[str]] = None,
        include_metadata: bool = True
    ) -> List[Dict]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            score_threshold: 相似度阈值
            file_extensions: 文件扩展名过滤
            include_metadata: 是否包含元数据
            
        Returns:
            搜索结果列表
        """
        try:
            # 构建过滤条件
            where_filter = {}
            if file_extensions:
                # ChromaDB的where条件格式
                if len(file_extensions) == 1:
                    where_filter["file_ext"] = file_extensions[0]
                else:
                    where_filter["file_ext"] = {"$in": file_extensions}
            
            # 执行相似性搜索
            if where_filter:
                results = self.vectorstore.similarity_search_with_score(
                    query=query,
                    k=k,
                    filter=where_filter
                )
            else:
                results = self.vectorstore.similarity_search_with_score(
                    query=query,
                    k=k
                )
            
            # 处理结果
            formatted_results = []
            for doc, score in results:
                if score >= score_threshold:
                    result = self._format_search_result(doc, score, query, include_metadata)
                    formatted_results.append(result)
            
            logger.info(f"语义搜索完成: 查询='{query}', 找到{len(formatted_results)}个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def search_by_filename(
        self,
        query: str,
        max_results: int = 30
    ) -> List[Dict]:
        """
        按文件名搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        try:
            # 获取所有文档的元数据
            collection = self.vectorstore._collection
            all_docs = collection.get()
            
            if not all_docs['metadatas']:
                return []
            
            # 文件名匹配
            matching_files = {}
            query_lower = query.lower()
            
            for i, metadata in enumerate(all_docs['metadatas']):
                if not metadata:
                    continue
                
                file_path = metadata.get('file_path', '')
                file_name = metadata.get('file_name', '')
                relative_path = metadata.get('relative_path', '')
                
                # 检查匹配
                score = 0
                if query_lower in file_name.lower():
                    score = 3  # 文件名完全匹配权重最高
                elif query_lower in relative_path.lower():
                    score = 2  # 路径匹配
                elif any(word in file_name.lower() for word in query_lower.split()):
                    score = 1  # 部分匹配
                
                if score > 0 and file_path not in matching_files:
                    matching_files[file_path] = {
                        'metadata': metadata,
                        'score': score,
                        'doc_id': all_docs['ids'][i] if all_docs['ids'] else None
                    }
            
            # 排序并格式化结果
            sorted_files = sorted(
                matching_files.values(),
                key=lambda x: (x['score'], x['metadata'].get('file_name', '')),
                reverse=True
            )
            
            results = []
            for item in sorted_files[:max_results]:
                metadata = item['metadata']
                result = {
                    'file_path': metadata.get('relative_path', ''),
                    'file_name': metadata.get('file_name', ''),
                    'file_extension': metadata.get('file_ext', ''),
                    'file_size': metadata.get('file_size', 0),
                    'modified_time': metadata.get('modified_time', ''),
                    'match_score': item['score'],
                    'match_type': 'filename'
                }
                results.append(result)
            
            logger.info(f"文件名搜索完成: 查询='{query}', 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"文件名搜索失败: {e}")
            return []
    
    def search_by_extension(
        self,
        extension: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        按文件扩展名搜索
        
        Args:
            extension: 文件扩展名
            limit: 结果限制
            
        Returns:
            文件列表
        """
        try:
            # 使用过滤器查询
            docs = self.vectorstore.get(
                where={"file_ext": extension},
                limit=limit
            )
            
            if not docs['metadatas']:
                return []
            
            # 去重并格式化结果
            unique_files = {}
            for metadata in docs['metadatas']:
                if not metadata:
                    continue
                
                file_path = metadata.get('file_path', '')
                if file_path not in unique_files:
                    unique_files[file_path] = {
                        'file_path': metadata.get('relative_path', ''),
                        'file_name': metadata.get('file_name', ''),
                        'file_extension': metadata.get('file_ext', ''),
                        'file_size': metadata.get('file_size', 0),
                        'modified_time': metadata.get('modified_time', ''),
                        'content_length': metadata.get('content_length', 0)
                    }
            
            results = list(unique_files.values())
            results.sort(key=lambda x: x['file_name'])
            
            logger.info(f"扩展名搜索完成: 扩展名='{extension}', 找到{len(results)}个文件")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"扩展名搜索失败: {e}")
            return []
    
    def get_similar_files(
        self,
        file_path: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        查找相似文件
        
        Args:
            file_path: 参考文件路径
            limit: 结果限制
            
        Returns:
            相似文件列表
        """
        try:
            path_obj = Path(file_path)
            file_name = path_obj.stem
            file_ext = path_obj.suffix
            
            # 先按扩展名过滤
            ext_results = self.search_by_extension(file_ext, limit * 3)
            
            # 计算相似度
            similar_files = []
            for result in ext_results:
                if result['file_path'] == file_path:
                    continue  # 排除自己
                
                similarity_score = self._calculate_filename_similarity(
                    file_name, Path(result['file_name']).stem
                )
                
                if similarity_score > 0:
                    result['similarity_score'] = similarity_score
                    result['similarity_reason'] = self._get_similarity_reason(
                        file_name, result['file_name'], file_ext
                    )
                    similar_files.append(result)
            
            # 排序并返回
            similar_files.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_files[:limit]
            
        except Exception as e:
            logger.error(f"查找相似文件失败: {e}")
            return []
    
    def _format_search_result(
        self,
        doc: Document,
        score: float,
        query: str,
        include_metadata: bool = True
    ) -> Dict:
        """格式化搜索结果"""
        metadata = doc.metadata
        content = doc.page_content
        
        result = {
            'content_snippet': content,
            'similarity_score': score,
            'file_path': metadata.get('relative_path', ''),
            'file_name': metadata.get('file_name', ''),
            'file_extension': metadata.get('file_ext', ''),
            'chunk_index': metadata.get('chunk_index', 0),
            'chunk_count': metadata.get('chunk_count', 1)
        }
        
        if include_metadata:
            result.update({
                'file_size': metadata.get('file_size', 0),
                'modified_time': metadata.get('modified_time', ''),
                'chunk_size': metadata.get('chunk_size', 0)
            })
        
        # 高亮匹配内容
        if query:
            highlighted_content = self._highlight_matches(content, query.split())
            result['highlighted_content'] = highlighted_content
        
        return result
    
    def _highlight_matches(self, content: str, query_words: List[str]) -> str:
        """高亮匹配的关键词"""
        highlighted = content
        
        for word in query_words:
            if len(word) >= 2:  # 只高亮长度>=2的词
                # 使用正则表达式进行大小写不敏感的替换
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted = pattern.sub(f'**{word.upper()}**', highlighted)
        
        return highlighted
    
    def _calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """计算文件名相似度"""
        if not name1 or not name2:
            return 0.0
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # 完全匹配
        if name1_lower == name2_lower:
            return 1.0
        
        # 包含关系
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.8
        
        # 词汇重叠
        words1 = set(re.findall(r'\w+', name1_lower))
        words2 = set(re.findall(r'\w+', name2_lower))
        
        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            jaccard = len(intersection) / len(union)
            
            if jaccard > 0.3:
                return jaccard * 0.6
        
        return 0.0
    
    def _get_similarity_reason(self, name1: str, name2: str, extension: str) -> str:
        """获取相似性原因描述"""
        reasons = []
        
        if extension:
            reasons.append(f"相同扩展名({extension})")
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        if name1_lower in name2_lower or name2_lower in name1_lower:
            reasons.append("文件名包含关系")
        
        words1 = set(re.findall(r'\w+', name1_lower))
        words2 = set(re.findall(r'\w+', name2_lower))
        common_words = words1.intersection(words2)
        
        if common_words:
            reasons.append(f"共同词汇: {', '.join(list(common_words)[:3])}")
        
        return "，".join(reasons) if reasons else "文件类型相似"
    
    async def hybrid_search(
        self,
        query: str,
        k: int = 30,
        file_extensions: Optional[List[str]] = None,
        include_filename_search: bool = True
    ) -> List[Dict]:
        """
        混合搜索：结合语义搜索和文件名搜索
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            file_extensions: 文件扩展名过滤
            include_filename_search: 是否包含文件名搜索
            
        Returns:
            搜索结果列表
        """
        try:
            results = []
            
            # 语义搜索
            semantic_results = await self.semantic_search(
                query=query,
                k=k,
                file_extensions=file_extensions
            )
            
            for result in semantic_results:
                result['search_type'] = 'semantic'
                results.append(result)
            
            # 文件名搜索
            if include_filename_search:
                filename_results = self.search_by_filename(
                    query=query,
                    max_results=k // 3
                )
                
                for result in filename_results:
                    result['search_type'] = 'filename'
                    # 转换格式以匹配语义搜索结果
                    result['similarity_score'] = result.get('match_score', 0) * 0.3
                    results.append(result)
            
            # 去重（基于文件路径）
            unique_results = {}
            for result in results:
                file_path = result.get('file_path', '')
                if file_path:
                    if file_path not in unique_results:
                        unique_results[file_path] = result
                    else:
                        # 保留评分更高的结果
                        existing_score = unique_results[file_path].get('similarity_score', 0)
                        current_score = result.get('similarity_score', 0)
                        if current_score > existing_score:
                            unique_results[file_path] = result
            
            # 排序
            final_results = list(unique_results.values())
            final_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            return final_results[:k]
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []

# 保持向后兼容性
CodebaseSearchEngine = VectorCodebaseSearchEngine 