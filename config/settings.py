# -*- coding: utf-8 -*-
"""
全局配置模块

提供应用程序的全局配置管理，支持从环境变量和.env文件加载配置。
配置项包括：模型API密钥、模型地址、温度参数、向量库路径、内存配置等。
"""

import os
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """大语言模型配置"""
    api_key: str = Field(default="", description="模型API密钥")
    base_url: str = Field(default="https://api.openai.com/v1", description="模型API地址")
    model_name: str = Field(default="gpt-4", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度参数")
    max_tokens: int = Field(default=2048, ge=1, description="最大生成token数")
    timeout: int = Field(default=60, ge=1, description="请求超时时间（秒）")
    streaming: bool = Field(default=False, description="是否启用流式输出")


class VectorStoreConfig(BaseModel):
    """向量库配置"""
    persist_directory: str = Field(default="./knowledge/vectorstore", description="向量库持久化目录")
    embedding_model: str = Field(default="text-embedding-ada-002", description="嵌入模型名称")
    embedding_dimension: int = Field(default=1536, description="嵌入向量维度")
    chunk_size: int = Field(default=500, description="文档分块大小")
    chunk_overlap: int = Field(default=50, description="文档分块重叠大小")


class MemoryConfig(BaseModel):
    """内存配置"""
    max_history: int = Field(default=100, description="最大对话历史条数")
    session_timeout: int = Field(default=3600, description="会话超时时间（秒）")
    memory_type: str = Field(default="buffer", description="内存类型：buffer/conversation_summary")


class KnowledgeConfig(BaseModel):
    """知识库配置"""
    supported_formats: list = Field(default_factory=lambda: [".txt", ".pdf", ".docx", ".md"], description="支持的文档格式")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小（字节）")
    index_name: str = Field(default="knowledge_base", description="知识库索引名称")


class LogConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    file_path: str = Field(default="./logs/app.log", description="日志文件路径")
    max_bytes: int = Field(default=10 * 1024 * 1024, description="日志文件最大大小")
    backup_count: int = Field(default=5, description="日志文件保留份数")
    console_output: bool = Field(default=True, description="是否输出到控制台")


class Settings(BaseSettings):
    """应用全局配置类"""
    project_name: str = Field(default="DevEnterpriseAI", description="项目名称")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="production", description="运行环境")

    # LLM配置
    llm_api_key: str = Field(default="", description="模型API密钥")
    llm_base_url: str = Field(default="https://api.openai.com/v1", description="模型API地址")
    llm_model_name: str = Field(default="gpt-4", description="模型名称")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度参数")
    llm_max_tokens: int = Field(default=2048, ge=1, description="最大生成token数")
    llm_timeout: int = Field(default=60, ge=1, description="请求超时时间（秒）")
    llm_streaming: bool = Field(default=False, description="是否启用流式输出")

    # VectorStore配置
    vectorstore_persist_directory: str = Field(default="./knowledge/vectorstore", description="向量库持久化目录")
    vectorstore_embedding_model: str = Field(default="text-embedding-ada-002", description="嵌入模型名称")
    vectorstore_embedding_dimension: int = Field(default=1536, description="嵌入向量维度")
    vectorstore_chunk_size: int = Field(default=500, description="文档分块大小")
    vectorstore_chunk_overlap: int = Field(default=50, description="文档分块重叠大小")

    # Memory配置
    memory_max_history: int = Field(default=100, description="最大对话历史条数")
    memory_session_timeout: int = Field(default=3600, description="会话超时时间（秒）")
    memory_memory_type: str = Field(default="buffer", description="内存类型：buffer/conversation_summary")

    # Knowledge配置
    knowledge_supported_formats: list = Field(default_factory=lambda: [".txt", ".pdf", ".docx", ".md"], description="支持的文档格式")
    knowledge_max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小（字节）")
    knowledge_index_name: str = Field(default="knowledge_base", description="知识库索引名称")

    # Log配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    log_file_path: str = Field(default="./logs/app.log", description="日志文件路径")
    log_max_bytes: int = Field(default=10 * 1024 * 1024, description="日志文件最大大小")
    log_backup_count: int = Field(default=5, description="日志文件保留份数")
    log_console_output: bool = Field(default=True, description="是否输出到控制台")

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"
        case_sensitive: bool = False
        extra: str = "ignore"

    @property
    def llm(self) -> LLMConfig:
        """获取LLM配置"""
        return LLMConfig(
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
            model_name=self.llm_model_name,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
            timeout=self.llm_timeout,
            streaming=self.llm_streaming,
        )

    @property
    def vectorstore(self) -> VectorStoreConfig:
        """获取VectorStore配置"""
        return VectorStoreConfig(
            persist_directory=self.vectorstore_persist_directory,
            embedding_model=self.vectorstore_embedding_model,
            embedding_dimension=self.vectorstore_embedding_dimension,
            chunk_size=self.vectorstore_chunk_size,
            chunk_overlap=self.vectorstore_chunk_overlap,
        )

    @property
    def memory(self) -> MemoryConfig:
        """获取Memory配置"""
        return MemoryConfig(
            max_history=self.memory_max_history,
            session_timeout=self.memory_session_timeout,
            memory_type=self.memory_memory_type,
        )

    @property
    def knowledge(self) -> KnowledgeConfig:
        """获取Knowledge配置"""
        return KnowledgeConfig(
            supported_formats=self.knowledge_supported_formats,
            max_file_size=self.knowledge_max_file_size,
            index_name=self.knowledge_index_name,
        )

    @property
    def log(self) -> LogConfig:
        """获取Log配置"""
        return LogConfig(
            level=self.log_level,
            format=self.log_format,
            file_path=self.log_file_path,
            max_bytes=self.log_max_bytes,
            backup_count=self.log_backup_count,
            console_output=self.log_console_output,
        )

    def model_post_init(self, __context: Any = None) -> None:
        """Pydantic v2 初始化后钩子，确保目录存在"""
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            self.vectorstore_persist_directory,
            Path(self.log_file_path).parent,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例实例

    Returns:
        Settings: 配置实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
