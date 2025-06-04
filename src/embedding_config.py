import os
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class EmbeddingConfig(BaseModel):
    """向量嵌入配置"""
    api_key: str = Field(..., description="OpenAI API密钥")
    base_url: str = Field(..., description="API基础URL")
    model_name: str = Field(default="BAAI/bge-m3", description="嵌入模型名称")
    chunk_size: int = Field(default=1000, description="文本分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠大小")
    max_retries: int = Field(default=3, description="API重试次数")
    
    class Config:
        env_prefix = "OPENAI_EMBEDDINGS_"

def get_embedding_config() -> EmbeddingConfig:
    """从环境变量获取嵌入配置"""
    try:
        config = EmbeddingConfig(
            api_key=os.getenv("OPENAI_EMBEDDINGS_API_KEY", ""),
            base_url=os.getenv("OPENAI_EMBEDDINGS_BASE_URL", ""),
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3"),
            chunk_size=int(os.getenv("EMBEDDING_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("EMBEDDING_CHUNK_OVERLAP", "200")),
            max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
        )
        
        if not config.api_key:
            raise ValueError("OPENAI_EMBEDDINGS_API_KEY 未设置")
        if not config.base_url:
            raise ValueError("OPENAI_EMBEDDINGS_BASE_URL 未设置")
            
        return config
        
    except Exception as e:
        logger.error(f"嵌入配置加载失败: {e}")
        raise

def create_embeddings_client(config: Optional[EmbeddingConfig] = None) -> OpenAIEmbeddings:
    """创建嵌入客户端"""
    if config is None:
        config = get_embedding_config()
    
    try:
        embeddings = OpenAIEmbeddings(
            openai_api_key=config.api_key,
            openai_api_base=config.base_url,
            model=config.model_name,
            max_retries=config.max_retries
        )
        
        logger.info(f"创建嵌入客户端成功: {config.model_name}")
        return embeddings
        
    except Exception as e:
        logger.error(f"创建嵌入客户端失败: {e}")
        raise

def test_embeddings_connection(embeddings: OpenAIEmbeddings) -> bool:
    """测试嵌入服务连接"""
    try:
        # 测试嵌入一小段文本
        test_text = "这是一个测试文本"
        result = embeddings.embed_query(test_text)
        
        if isinstance(result, list) and len(result) > 0:
            logger.info(f"嵌入服务连接正常，向量维度: {len(result)}")
            return True
        else:
            logger.error("嵌入服务返回无效结果")
            return False
            
    except Exception as e:
        logger.error(f"嵌入服务连接测试失败: {e}")
        return False 