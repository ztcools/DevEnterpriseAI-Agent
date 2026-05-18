# -*- coding: utf-8 -*-
"""
全局配置模块

提供应用程序的全局配置管理，支持从环境变量和.env文件加载配置。
配置项包括：模型API密钥、模型地址、温度参数、向量库路径、内存配置等。
"""

import os
from pathlib import Path
from typing import Optional
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

    llm: LLMConfig = Field(default_factory=LLMConfig, description="大语言模型配置")
    vectorstore: VectorStoreConfig = Field(default_factory=VectorStoreConfig, description="向量库配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存配置")
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig, description="知识库配置")
    log: LogConfig = Field(default_factory=LogConfig, description="日志配置")

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"
        case_sensitive: bool = False
        extra: str = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            self.vectorstore.persist_directory,
            Path(self.log.file_path).parent,
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
