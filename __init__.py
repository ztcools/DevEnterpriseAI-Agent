# -*- coding: utf-8 -*-
"""
DevEnterpriseAI - 企业私有化AI开发Agent

企业级AI应用开发框架，支持私有化大模型部署。
"""

__version__ = "0.1.0"
__author__ = "EnterpriseAI Team"

from config import get_settings, Settings
from core import (
    LLMFactory,
    EnterpriseLLM,
    EmbeddingsClient,
    ConversationMemory,
    MemoryFactory,
    DevEnterpriseAgent,
    create_agent,
)
from tools import (
    BaseTool,
    ToolFactory,
    register_tool,
    CodeGeneratorTool,
    CodeRefactorTool,
    CompileErrorAnalyzerTool,
    DocGeneratorTool,
    ScriptGeneratorTool,
)
from knowledge import KnowledgeIngestor, DocumentLoader, RAGRetriever, create_ingestor, create_retriever
from utils import (
    setup_logger,
    get_logger,
    EnterpriseAIException,
    ConfigurationError,
    LLMError,
    ToolExecutionError,
    KnowledgeBaseError,
    NetworkError,
    ValidationError,
)

__all__ = [
    "get_settings",
    "Settings",
    "LLMFactory",
    "EnterpriseLLM",
    "EmbeddingsClient",
    "ConversationMemory",
    "MemoryFactory",
    "DevEnterpriseAgent",
    "create_agent",
    "BaseTool",
    "ToolFactory",
    "register_tool",
    "CodeGeneratorTool",
    "CodeRefactorTool",
    "CompileErrorAnalyzerTool",
    "DocGeneratorTool",
    "ScriptGeneratorTool",
    "KnowledgeIngestor",
    "DocumentLoader",
    "RAGRetriever",
    "create_ingestor",
    "create_retriever",
    "setup_logger",
    "get_logger",
    "EnterpriseAIException",
    "ConfigurationError",
    "LLMError",
    "ToolExecutionError",
    "KnowledgeBaseError",
    "NetworkError",
    "ValidationError",
]
