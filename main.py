import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

mcp = FastMCP("简化文件读取 MCP 服务器", host="0.0.0.0", port=3002)

# 然后导入自定义模块
from src import (
    UniversalFileReader, DocumentCache, FileConverter, get_config_manager,
    VectorCodebaseIndexer, VectorCodebaseSearchEngine, IndexScheduler,
    get_embedding_config, create_embeddings_client
)
from src.dir_tree import get_dir_tree_markdown


# 配置日志系统
def setup_logging():
    """配置日志系统"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            )
        ]
    )
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

logger = setup_logging()

# 添加src目录到路径
sys.path.insert(0, 'src')


# 全局变量 - 延迟初始化
global_indexer = None
global_search_engine = None
global_scheduler = None

def init_search_components():
    """初始化搜索组件"""
    global global_indexer, global_search_engine, global_scheduler
    
    if global_indexer is None:
        try:
            # 测试嵌入服务连接
            embedding_config = get_embedding_config()
            embeddings = create_embeddings_client(embedding_config)
            
            # 测试连接
            test_result = embeddings.embed_query("测试连接")
            if not test_result:
                raise ValueError("嵌入服务连接失败")
            
            logger.info(f"嵌入服务连接成功，向量维度: {len(test_result)}")
            
            # 初始化组件
            global_indexer = VectorCodebaseIndexer()
            global_search_engine = VectorCodebaseSearchEngine(global_indexer)
            global_scheduler = IndexScheduler(global_indexer)
            
            # 启动调度器
            global_scheduler.start()
            
            logger.info("向量搜索组件初始化完成")
            
        except Exception as e:
            logger.error(f"搜索组件初始化失败: {e}")
            raise

@mcp.tool("view_directory_tree")
async def view_directory_tree(
    directory_path: str = ".",
    max_depth: int = 3,
    max_entries: int = 300
) -> str:
    """查看目录树结构"""
    try:
        logger.info(f"🔧 收到调用请求: directory_path={directory_path}")
        
        # 直接创建文件读取器实例
        file_reader = UniversalFileReader()
        
        # 获取安全目录
        safe_directory = file_reader.validator.get_safe_directory()
        logger.info(f"🔧 安全目录: {safe_directory}")
        
        # 处理路径 - 修复路径解析逻辑
        if os.path.isabs(directory_path):
            # 绝对路径，直接使用并规范化
            abs_path = str(Path(directory_path).resolve())
        else:
            # 相对路径，基于安全目录进行解析
            safe_path = Path(safe_directory).resolve()
            target_path = safe_path / directory_path
            abs_path = str(target_path.resolve())
        
        logger.info(f"📂 最终路径: {abs_path}")
        
        # 简单检查 - 先检查基本条件再进行安全验证
        if not os.path.exists(abs_path):
            logger.error(f"❌ 路径不存在: {abs_path}")
            return f"❌ 路径不存在: {abs_path}"
            
        if not os.path.isdir(abs_path):
            logger.error(f"❌ 不是目录: {abs_path}")
            return f"❌ 不是目录: {abs_path}"
        
        # 安全验证 - 简化验证过程
        try:
            # 检查路径是否在安全目录内（简化版本）
            safe_abs = Path(safe_directory).resolve()
            target_abs = Path(abs_path).resolve()
            try:
                target_abs.relative_to(safe_abs)
            except ValueError:
                logger.error(f"❌ 路径不在安全目录内: {abs_path}")
                return f"❌ 路径不在安全目录内"
        except Exception as e:
            logger.error(f"❌ 路径安全验证失败: {abs_path}, 错误: {e}")
            return f"❌ 路径安全验证失败: {e}"
        
        # 使用 run_in_executor 避免阻塞
        tree_content = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: get_dir_tree_markdown(abs_path, max_depth, max_entries)
        )
        logger.info(f"🌳 生成完成，长度: {len(tree_content)}")
        
        result = f"🌳 目录: {abs_path}\n\n{tree_content}"
        logger.info(f"✅ 返回结果，长度: {len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 函数执行错误: {str(e)}")
        return f"❌ 错误: {str(e)}"

@mcp.tool("list_files")
async def list_files(
    directory_path: str = ".",
    pattern: str = "*",
    include_size: bool = True
) -> str:
    """列出目录中的文件"""
    try:
        # 直接创建文件读取器实例
        file_reader = UniversalFileReader()
        
        # 获取安全目录
        safe_directory = file_reader.validator.get_safe_directory()
        
        # 处理路径
        if os.path.isabs(directory_path):
            abs_path = str(Path(directory_path).resolve())
        else:
            safe_path = Path(safe_directory).resolve()
            target_path = safe_path / directory_path
            abs_path = str(target_path.resolve())
        
        # 安全验证
        if not os.path.exists(abs_path):
            return f"❌ 路径不存在: {abs_path}"
            
        if not os.path.isdir(abs_path):
            return f"❌ 不是目录: {abs_path}"
        
        # 安全验证
        try:
            safe_abs = Path(safe_directory).resolve()
            target_abs = Path(abs_path).resolve()
            try:
                target_abs.relative_to(safe_abs)
            except ValueError:
                return f"❌ 路径不在安全目录内"
        except Exception as e:
            return f"❌ 路径安全验证失败: {e}"
        
        # 获取文件列表
        import glob
        pattern_path = os.path.join(abs_path, pattern)
        files = glob.glob(pattern_path)
        
        # 过滤出文件（排除目录）
        files = [f for f in files if os.path.isfile(f)]
        files.sort()
        
        if not files:
            return f"📁 目录: {abs_path}\n无匹配的文件"
        
        # 格式化输出
        result = f"📁 目录: {abs_path}\n"
        result += f"📄 文件列表 ({len(files)}个文件):\n"
        result += "=" * 50 + "\n"
        
        for file_path in files:
            rel_path = os.path.relpath(file_path, abs_path)
            if include_size:
                size = os.path.getsize(file_path)
                result += f"📄 {rel_path} ({size:,} 字节)\n"
            else:
                result += f"📄 {rel_path}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 列出文件失败: {str(e)}")
        return f"❌ 错误: {str(e)}"

@mcp.tool("read_file_content")
async def read_file_range(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None
) -> str:
    """读取文件内容，支持指定行范围。自动处理文档文件转换和缓存。"""
    try:
        # 直接创建实例
        file_reader = UniversalFileReader()
        doc_cache = DocumentCache()
        
        # 获取安全目录
        safe_directory = file_reader.validator.get_safe_directory()
        
        # 处理相对路径和绝对路径
        if os.path.isabs(file_path):
            # 绝对路径直接使用
            abs_path = str(Path(file_path).resolve())
        else:
            # 相对路径拼接到安全目录，不使用当前工作目录
            abs_path = str(Path(safe_directory) / file_path)
        
        # 安全验证
        file_reader.validator.validate_file_path(abs_path)
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {file_path}"
        
        # 获取文件信息
        file_info = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: file_reader.get_file_info(abs_path)
        )
        
        # 检查是否是文档文件（需要转换）
        if file_info.get('is_document_file', False):
            # 尝试从缓存获取
            cached_content = doc_cache.get_cached_content(abs_path)
            
            if cached_content is not None:
                # 使用缓存内容
                content = cached_content
                cache_used = True
            else:
                # 转换文档并缓存
                file_ext = Path(abs_path).suffix.lower()
                converter = FileConverter.get_converter_for_extension(file_ext)
                
                if converter is None:
                    return f"❌ 不支持的文档格式: {file_ext}"
                
                content = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: converter(abs_path)
                )
                
                # 缓存转换结果
                doc_cache.cache_content(abs_path, content)
                cache_used = False
        else:
            # 直接读取文本文件
            content = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: file_reader.read_file(abs_path, start_line, end_line)
            )
            cache_used = False
        
        # 如果是文本文件且指定了行范围，需要截取对应行
        if not file_info.get('is_document_file', False) and (start_line > 1 or end_line is not None):
            lines = content.split('\n')
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line) if end_line else len(lines)
            content = '\n'.join(lines[start_idx:end_idx])
            actual_lines = end_idx - start_idx
        else:
            actual_lines = len(content.split('\n')) if content else 0
        
        # 格式化输出
        result = f"📄 文件读取成功\n"
        result += f"{'=' * 50}\n"
        result += f"📁 文件路径: {abs_path}\n"
        result += f"📊 文件大小: {file_info['size']:,} 字节\n"
        result += f"📝 文件类型: {'文档文件' if file_info.get('is_document_file') else '文本文件'}"
        
        if file_info.get('is_document_file'):
            result += f" ({'使用缓存' if cache_used else '重新转换'})"
        result += f"\n🔤 文件编码: {file_info.get('detected_encoding', '未检测')}\n"
        
        # 显示读取范围（仅对文本文件有效）
        if not file_info.get('is_document_file', False):
            total_lines = file_info.get('total_lines', 0)
            if end_line:
                result += f"📖 读取范围: 第{start_line}-{min(end_line, total_lines)}行\n"
            else:
                result += f"📖 读取范围: 第{start_line}行到末尾\n"
        else:
            result += f"📖 文档转换: 已转换为Markdown格式\n"
            
        result += f"📋 内容长度: {actual_lines}行，{len(content):,}字符\n\n"
        result += f"{'=' * 50}\n"
        result += f"📄 文件内容:\n\n"
        result += content
        
        logger.info(f"文件读取成功: {file_path}, 行范围: {start_line}-{end_line or '末尾'}")
        return result
        
    except Exception as e:
        logger.error(f"文件读取失败: {file_path}, 错误: {e}")
        return f"❌ 文件读取失败: {e}"

@mcp.tool("preview_file")
async def preview_file(
    file_path: str,
    lines: int = 20
) -> str:
    """快速预览文件前N行内容"""
    try:
        # 直接创建实例
        file_reader = UniversalFileReader()
        
        # 获取安全目录
        safe_directory = file_reader.validator.get_safe_directory()
        
        # 处理相对路径和绝对路径
        if os.path.isabs(file_path):
            abs_path = str(Path(file_path).resolve())
        else:
            abs_path = str(Path(safe_directory) / file_path)
        
        # 安全验证
        file_reader.validator.validate_file_path(abs_path)
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {file_path}"
        
        # 读取指定行数
        content = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: file_reader.read_file(abs_path, 1, lines)
        )
        
        # 获取文件信息
        file_info = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: file_reader.get_file_info(abs_path)
        )
        
        total_lines = file_info.get('total_lines', 0)
        result = f"📄 文件预览: {abs_path}\n"
        result += f"📊 前{lines}行 / 总{total_lines}行\n"
        result += "=" * 50 + "\n"
        result += content
        
        if total_lines > lines:
            result += f"\n... (还有{total_lines - lines}行)"
        
        return result
        
    except Exception as e:
        logger.error(f"文件预览失败: {file_path}, 错误: {e}")
        return f"❌ 文件预览失败: {e}"

@mcp.tool("search_documents")
async def search_codebase(
    query: str,
    search_type: str = "semantic",
    file_extensions: Optional[str] = None,
    max_results: int = 10
) -> str:
    """智能搜索文档知识库。支持语义搜索(semantic)、文件名搜索(filename)、混合搜索(hybrid)。"""
    try:
        # 初始化搜索组件
        init_search_components()
        
        logger.info(f"🔍 向量搜索请求: query='{query}', type={search_type}, extensions={file_extensions}")
        
        # 解析文件扩展名
        extensions_list = None
        if file_extensions:
            extensions_list = [ext.strip() for ext in file_extensions.split(',') if ext.strip()]
        
        # 根据搜索类型执行不同的搜索
        if search_type == "semantic":
            results = await global_search_engine.semantic_search(
                query=query,
                k=max_results,
                file_extensions=extensions_list,
                include_metadata=True
            )
        elif search_type == "filename":
            results = global_search_engine.search_by_filename(
                query=query,
                max_results=max_results
            )
        elif search_type == "extension":
            if not extensions_list or len(extensions_list) != 1:
                return "❌ 按扩展名搜索时，请指定单个文件扩展名，如: file_extensions='.py'"
            
            results = global_search_engine.search_by_extension(
                extension=extensions_list[0],
                limit=max_results
            )
        elif search_type == "hybrid":
            results = await global_search_engine.hybrid_search(
                query=query,
                k=max_results,
                file_extensions=extensions_list,
                include_filename_search=True
            )
        else:
            return f"❌ 不支持的搜索类型: {search_type}，支持: semantic, filename, extension, hybrid"
        
        if not results:
            return f"🔍 文档搜索完成，未找到匹配的结果\n\n" \
                   f"搜索条件：\n" \
                   f"- 查询: {query}\n" \
                   f"- 搜索类型: {search_type}\n" \
                   f"- 文件扩展名: {file_extensions or '不限制'}\n\n" \
                   f"💡 建议：\n" \
                   f"- 尝试更通用的关键词或概念\n" \
                   f"- 使用hybrid搜索获得更全面的结果\n" \
                   f"- 使用filename搜索查找特定文件\n" \
                   f"- 检查索引是否需要重建"
        
        # 格式化输出结果
        result_text = f"🔍 文档搜索结果 ({len(results)}个匹配)\n"
        result_text += f"{'=' * 60}\n"
        result_text += f"🎯 搜索查询: {query}\n"
        result_text += f"🔧 搜索类型: {search_type}\n"
        if file_extensions:
            result_text += f"📁 文件类型: {file_extensions}\n"
        result_text += f"📊 结果数量: {len(results)}/{max_results}\n\n"
        
        for i, result in enumerate(results, 1):
            result_text += f"📄 [{i}] {result.get('file_name', '未知文件')}\n"
            result_text += f"📁 路径: {result.get('file_path', '')}\n"
            
            # 显示相似度评分
            if 'similarity_score' in result:
                score = result['similarity_score']
                result_text += f"🎯 相似度: {score:.3f}\n"
            
            # 显示搜索类型
            if 'search_type' in result:
                result_text += f"🔍 匹配类型: {result['search_type']}\n"
            
            # 显示文件信息
            if 'file_size' in result:
                result_text += f"📦 大小: {result['file_size']:,} 字节\n"
            
            # 显示内容片段（语义搜索）
            if search_type in ["semantic", "hybrid"] and result.get('content_snippet'):
                snippet = result['content_snippet']
                if len(snippet) > 150:
                    snippet = snippet[:150] + "..."
                result_text += f"📖 内容片段:\n   {snippet.replace(chr(10), ' ')}\n"
                
                # 显示高亮内容
                if result.get('highlighted_content'):
                    highlighted = result['highlighted_content']
                    if len(highlighted) > 200:
                        highlighted = highlighted[:200] + "..."
                    result_text += f"✨ 高亮匹配:\n   {highlighted.replace(chr(10), ' ')}\n"
            
            # 显示匹配原因（文件名搜索）
            if result.get('match_type'):
                result_text += f"🎪 匹配类型: {result['match_type']}\n"
            
            # 显示相似原因（相似文件搜索）
            if result.get('similarity_reason'):
                result_text += f"🔗 相似原因: {result['similarity_reason']}\n"
            
            # 显示分块信息（语义搜索）
            if 'chunk_index' in result and 'chunk_count' in result:
                result_text += f"📝 文档片段: {result['chunk_index'] + 1}/{result['chunk_count']}\n"
            
            if 'modified_time' in result:
                result_text += f"⏰ 修改时间: {result['modified_time']}\n"
            
            result_text += f"{'-' * 40}\n"
        
        # 添加搜索提示
        if search_type == "semantic":
            result_text += f"\n💡 语义搜索提示：搜索结果按语义相似度排序，可以理解概念和上下文关系\n"
        elif search_type == "hybrid":
            result_text += f"\n💡 混合搜索提示：结合了语义理解和文件名匹配，获得最全面的搜索结果\n"
        
        logger.info(f"✅ 文档搜索完成: 找到{len(results)}个结果")
        return result_text
        
    except Exception as e:
        logger.error(f"❌ 文档搜索失败: {e}")
        return f"❌ 文档搜索失败: {e}\n\n可能的原因：\n- 嵌入服务连接问题\n- 索引未建立或损坏\n- 配置错误"

@mcp.tool("rebuild_document_index")
async def rebuild_codebase_index() -> str:
    """重建文档知识库向量索引用于语义搜索"""
    try:
        # 初始化搜索组件
        init_search_components()
        
        logger.info("🔄 手动触发向量索引重建")
        
        # 执行重建
        result = await global_scheduler.manual_rebuild()
        
        # 获取统计信息
        stats = global_indexer.get_index_stats()
        
        # 格式化输出
        output = f"✅ 文档知识库向量索引重建完成\n"
        output += f"{'=' * 50}\n"
        output += f"📊 重建统计:\n"
        output += f"   🔍 扫描文件: {result['scanned_files']:,} 个\n"
        output += f"   📝 索引文件: {result['indexed_files']:,} 个\n"
        output += f"   📄 生成文档: {result['total_documents']:,} 个\n"
        output += f"   📝 文档块数: {result['indexed_chunks']:,} 个\n"
        output += f"   ⏱️ 总耗时: {result['duration_seconds']:.2f} 秒\n\n"
        
        output += f"📈 索引统计:\n"
        output += f"   📄 总文档数: {stats['total_documents']:,} 个\n"
        output += f"   📁 总文件数: {stats['total_files']:,} 个\n"
        output += f"   🗂️ 存储目录: {stats['persist_directory']}\n"
        output += f"   🧠 嵌入模型: {stats['embedding_model']}\n"
        output += f"   📏 分块大小: {stats['chunk_size']} 字符\n\n"
        
        if stats.get('extension_stats'):
            output += f"📁 文件类型分布:\n"
            for ext, count in list(stats['extension_stats'].items())[:10]:
                output += f"   {ext or '(无扩展名)'}: {count:,} 个文档块\n"
        
        output += f"\n🎯 向量索引已更新，可以使用 search_documents 工具进行语义搜索\n"
        output += f"💡 建议：首次建立索引后，可以尝试用自然语言描述查找文档内容"
        
        logger.info(f"✅ 向量索引重建完成: {result}")
        return output
        
    except Exception as e:
        logger.error(f"❌ 向量索引重建失败: {e}")
        return f"❌ 向量索引重建失败: {e}\n\n可能的原因：\n- 嵌入服务连接问题\n- 文件访问权限问题\n- 磁盘空间不足\n- 配置错误"

@mcp.tool("get_document_stats")
async def get_codebase_stats() -> str:
    """获取文档知识库索引统计信息和状态"""
    try:
        # 初始化搜索组件
        init_search_components()
        
        # 获取索引统计
        index_stats = global_indexer.get_index_stats()
        
        # 获取调度器状态
        scheduler_stats = global_scheduler.get_status()
        
        # 获取嵌入配置
        embedding_config = global_indexer.embedding_config
        
        # 格式化输出
        output = f"📊 文档知识库向量索引统计信息\n"
        output += f"{'=' * 60}\n\n"
        
        # 基本统计
        output += f"📈 基本统计:\n"
        output += f"   📄 总文档数: {index_stats['total_documents']:,} 个\n"
        output += f"   📁 总文件数: {index_stats['total_files']:,} 个\n"
        output += f"   🗂️ 存储目录: {index_stats['persist_directory']}\n"
        output += f"   📏 分块大小: {index_stats['chunk_size']} 字符\n\n"
        
        # 嵌入配置
        output += f"🧠 嵌入配置:\n"
        output += f"   🤖 模型名称: {index_stats['embedding_model']}\n"
        output += f"   🌐 API地址: {embedding_config.base_url}\n"
        output += f"   📏 分块大小: {embedding_config.chunk_size} 字符\n"
        output += f"   🔄 重叠大小: {embedding_config.chunk_overlap} 字符\n"
        output += f"   🔁 重试次数: {embedding_config.max_retries}\n\n"
        
        # 文件类型分布
        if index_stats.get('extension_stats'):
            output += f"📁 文件类型分布 (前10):\n"
            total_docs = index_stats['total_documents']
            for ext, count in list(index_stats['extension_stats'].items())[:10]:
                percentage = (count / total_docs) * 100 if total_docs > 0 else 0
                output += f"   {ext or '(无扩展名)'}: {count:,} 个文档块 ({percentage:.1f}%)\n"
        
        output += f"\n"
        
        # 调度器状态
        output += f"🔄 调度器状态:\n"
        output += f"   🟢 运行状态: {'运行中' if scheduler_stats['running'] else '已停止'}\n"
        output += f"   ⏱️ 索引间隔: {scheduler_stats['index_interval_hours']} 小时\n"
        output += f"   📅 计划任务: {scheduler_stats['scheduled_jobs']} 个\n"
        
        if scheduler_stats.get('last_index_time'):
            output += f"   🕐 上次索引: {scheduler_stats['last_index_time']}\n"
        
        if scheduler_stats.get('next_run_time'):
            output += f"   ⏰ 下次运行: {scheduler_stats['next_run_time']}\n"
        
        output += f"   🧵 线程状态: {'活跃' if scheduler_stats['thread_alive'] else '非活跃'}\n"
        
        # 检查系统健康度
        output += f"\n💡 系统状态:\n"
        
        if index_stats['total_documents'] == 0:
            output += f"   ⚠️ 向量索引为空，建议运行 rebuild_document_index 建立索引\n"
        elif not scheduler_stats['running']:
            output += f"   ⚠️ 调度器未运行，索引可能不会自动更新\n"
        else:
            output += f"   ✅ 向量索引状态正常，支持语义搜索功能\n"
        
        # 测试嵌入服务连接
        try:
            test_result = global_indexer.embeddings.embed_query("测试")
            if test_result and len(test_result) > 0:
                output += f"   ✅ 嵌入服务连接正常，向量维度: {len(test_result)}\n"
            else:
                output += f"   ⚠️ 嵌入服务响应异常\n"
        except Exception as e:
            output += f"   ❌ 嵌入服务连接失败: {e}\n"
        
        if index_stats.get('error'):
            output += f"\n❌ 错误信息: {index_stats['error']}\n"
        
        # 使用建议
        output += f"\n🎯 使用建议:\n"
        output += f"   • 使用 search_documents 进行语义搜索\n"
        output += f"   • 尝试用自然语言描述要查找的文档内容\n"
        output += f"   • 定期重建索引以保持最新状态\n"
        output += f"   • 语义搜索比传统关键词匹配更智能\n"
        
        return output
        
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        return f"❌ 获取统计信息失败: {e}"

async def auto_index_on_startup():
    """启动时自动进行文档知识库索引"""
    try:
        logger.info("🚀 检查文档知识库索引状态...")
        
        # 初始化搜索组件
        init_search_components()
        
        # 获取当前索引统计
        stats = global_indexer.get_index_stats()
        
        # 如果没有索引，直接重建
        if stats['total_documents'] == 0:
            print("\n🔧 首次启动，正在建立文档知识库索引...")
            print("=" * 60)
            
            # 执行索引重建
            result = await global_indexer.rebuild_index()
            
            print("=" * 60)
            print(f"✅ 索引建立完成！")
            print(f"   📁 扫描文件: {result['scanned_files']} 个")
            print(f"   📝 索引文件: {result['indexed_files']} 个")  
            print(f"   📄 生成文档: {result['total_documents']} 个")
            print(f"   ⏱️ 总耗时: {result['duration_seconds']:.1f} 秒")
            print("🎯 现在可以使用智能文档搜索功能了！\n")
            return
        
        # 如果有现有索引，检查是否需要更新
        logger.info(f"✅ 发现现有索引: {stats['total_documents']} 个文档，{stats['total_files']} 个文件")
        
        # 扫描目录获取当前文件列表
        print("🔍 检查文件变化...")
        current_files = await asyncio.get_event_loop().run_in_executor(
            None, global_indexer._scan_directory, global_indexer.safe_directory
        )
        
        # 获取已索引的文件信息
        collection = global_indexer.vectorstore._collection
        existing_docs = collection.get()
        
        indexed_files = {}
        if existing_docs['metadatas']:
            for metadata in existing_docs['metadatas']:
                if metadata and 'file_path' in metadata:
                    file_path = metadata['file_path']
                    if file_path not in indexed_files:
                        indexed_files[file_path] = metadata.get('file_hash', '')
        
        # 检查新文件和变更文件
        new_files = []
        changed_files = []
        
        for file_path in current_files:
            current_hash = global_indexer._get_file_hash(file_path)
            
            if file_path not in indexed_files:
                # 新文件
                new_files.append(file_path)
            elif indexed_files[file_path] != current_hash:
                # 文件已变更
                changed_files.append(file_path)
        
        # 检查是否有文件被删除
        deleted_files = []
        for indexed_file in indexed_files.keys():
            if indexed_file not in current_files:
                deleted_files.append(indexed_file)
        
        # 判断是否需要更新索引
        total_changes = len(new_files) + len(changed_files) + len(deleted_files)
        
        if total_changes == 0:
            print(f"✅ 文档知识库索引已是最新: {stats['total_documents']} 个文档，{stats['total_files']} 个文件")
            return
        
        # 有变化，需要更新索引
        print(f"\n🔄 检测到文件变化，正在更新索引...")
        print("=" * 60)
        print(f"📊 变化统计:")
        if new_files:
            print(f"   ➕ 新增文件: {len(new_files)} 个")
            for file_path in new_files[:3]:  # 只显示前3个
                print(f"      • {Path(file_path).name}")
            if len(new_files) > 3:
                print(f"      • ... 还有 {len(new_files) - 3} 个文件")
        
        if changed_files:
            print(f"   🔄 变更文件: {len(changed_files)} 个")
            for file_path in changed_files[:3]:  # 只显示前3个
                print(f"      • {Path(file_path).name}")
            if len(changed_files) > 3:
                print(f"      • ... 还有 {len(changed_files) - 3} 个文件")
        
        if deleted_files:
            print(f"   ❌ 删除文件: {len(deleted_files)} 个")
            for file_path in deleted_files[:3]:  # 只显示前3个
                print(f"      • {Path(file_path).name}")
            if len(deleted_files) > 3:
                print(f"      • ... 还有 {len(deleted_files) - 3} 个文件")
        
        print("=" * 60)
        
        # 执行索引重建（会自动处理新增、变更和删除）
        result = await global_indexer.rebuild_index()
        
        print("=" * 60)
        print(f"✅ 索引更新完成！")
        print(f"   📁 扫描文件: {result['scanned_files']} 个")
        print(f"   📝 索引文件: {result['indexed_files']} 个")  
        print(f"   📄 生成文档: {result['total_documents']} 个")
        print(f"   ⏱️ 总耗时: {result['duration_seconds']:.1f} 秒")
        print("🎯 文档知识库已更新到最新状态！\n")
        
    except Exception as e:
        logger.error(f"❌ 自动索引失败: {e}")
        print(f"❌ 自动索引失败: {e}")
        print("💡 您可以稍后使用 rebuild_document_index 工具手动建立索引")

if __name__ == "__main__":
    """主函数，启动MCP服务器"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 启动简化文件读取 MCP 服务器")
        logger.info("=" * 60)
        
        # 获取配置信息
        current_config_manager = get_config_manager()
        safe_dir = current_config_manager.get_safe_directory()
        
        # 验证配置
        if not os.path.exists(safe_dir):
            logger.warning(f"⚠️  安全目录不存在: {safe_dir}")
        else:
            logger.info(f"✅ 安全目录验证通过: {safe_dir}")
        
        # 验证组件状态
        logger.info("🔍 验证组件状态...")
        
        # 测试文件读取器
        try:
            test_file_reader = UniversalFileReader()
            test_dir = test_file_reader.validator.get_safe_directory()
            logger.info(f"✅ 文件读取器工作正常: {test_dir}")
        except Exception as e:
            logger.error(f"❌ 文件读取器验证失败: {e}")
            raise
        
        # 测试缓存管理器
        try:
            test_doc_cache = DocumentCache()
            # 使用字符串形式而不是访问可能未初始化的 cache_dir
            cache_path = str(test_doc_cache.cache_dir)
            logger.info(f"✅ 缓存管理器工作正常: {cache_path}")
        except Exception as e:
            logger.error(f"❌ 缓存管理器验证失败: {e}")
            raise
        
        # 输出配置信息
        logger.info(f"🔧 安全目录: {safe_dir}")
        logger.info(f"💾 缓存目录: {cache_path}")
        logger.info(f"🛠️  可用工具: 目录树查看、文件内容读取、智能搜索")

        logger.info("🎯 所有组件验证完成，正在启动服务器...")
        
        # 启动时自动进行代码库索引
        import asyncio
        asyncio.run(auto_index_on_startup())
        
        # 使用FastMCP 2.0的正确启动方式
        logger.info("🚀 启动 MCP 服务器...")
        mcp.run(transport="sse")
        
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭服务器...")
        print("\n👋 服务器已停止")
    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {e}")
        print(f"❌ 模块导入失败: {e}")
        print("请检查所有依赖模块是否正确安装")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        print(f"❌ 服务器启动失败: {e}")
        print("请检查配置文件和依赖项")
        sys.exit(1)
    finally:
        logger.info("🔚 服务器已关闭")
        logger.info("=" * 60)
