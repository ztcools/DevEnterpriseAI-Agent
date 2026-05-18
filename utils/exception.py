# -*- coding: utf-8 -*-
"""
异常定义模块

定义应用程序的异常类体系，包括配置错误、LLM错误、工具执行错误、知识库错误等。
采用层次化的异常设计，便于错误捕获和处理。
"""


class EnterpriseAIException(Exception):
    """企业AI基础异常类

    所有自定义异常的基类。
    """

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None):
        """初始化异常

        Args:
            message: 异常消息
            code: 异常代码
            details: 异常详情
        """
        super().__init__(message)
        self.message = message
        self.code = code or "EAI_UNKNOWN"
        self.details = details or {}

    def __str__(self) -> str:
        """字符串表示"""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """转换为字典格式

        Returns:
            dict: 异常信息字典
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class ConfigurationError(EnterpriseAIException):
    """配置错误异常

    当配置项缺失、无效或读取失败时抛出。
    """

    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[dict] = None):
        """初始化配置错误

        Args:
            message: 异常消息
            config_key: 配置项键名
            details: 异常详情
        """
        super().__init__(message, code="EAI_CONFIG", details=details)
        self.config_key = config_key

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        if self.config_key:
            return f"{base_str} (config_key: {self.config_key})"
        return base_str


class LLMError(EnterpriseAIException):
    """大语言模型错误异常

    当LLM调用失败、响应解析错误或模型服务不可用时抛出。
    """

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        error_type: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """初始化LLM错误

        Args:
            message: 异常消息
            model_name: 模型名称
            error_type: 错误类型（timeout、rate_limit、api_error等）
            details: 异常详情
        """
        super().__init__(message, code="EAI_LLM", details=details)
        self.model_name = model_name
        self.error_type = error_type or "unknown"

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        parts = [base_str]
        if self.model_name:
            parts.append(f"model: {self.model_name}")
        if self.error_type:
            parts.append(f"error_type: {self.error_type}")
        return f"{base_str} ({'; '.join(parts)})"


class ToolExecutionError(EnterpriseAIException):
    """工具执行错误异常

    当自定义工具执行失败时抛出。
    """

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[dict] = None,
        details: Optional[dict] = None
    ):
        """初始化工具执行错误

        Args:
            message: 异常消息
            tool_name: 工具名称
            tool_input: 工具输入参数
            details: 异常详情
        """
        super().__init__(message, code="EAI_TOOL", details=details)
        self.tool_name = tool_name
        self.tool_input = tool_input

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        if self.tool_name:
            return f"{base_str} (tool: {self.tool_name})"
        return base_str


class KnowledgeBaseError(EnterpriseAIException):
    """知识库错误异常

    当知识库操作失败时抛出，包括文档加载、分块、向量化、检索等操作。
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        file_path: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """初始化知识库错误

        Args:
            message: 异常消息
            operation: 操作类型（load、split、embed、search等）
            file_path: 相关文件路径
            details: 异常详情
        """
        super().__init__(message, code="EAI_KB", details=details)
        self.operation = operation
        self.file_path = file_path

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        parts = []
        if self.operation:
            parts.append(f"operation: {self.operation}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")
        if parts:
            return f"{base_str} ({'; '.join(parts)})"
        return base_str


class AuthenticationError(EnterpriseAIException):
    """认证错误异常

    当API密钥无效、权限不足或认证失败时抛出。
    """

    def __init__(self, message: str, api_endpoint: Optional[str] = None, details: Optional[dict] = None):
        """初始化认证错误

        Args:
            message: 异常消息
            api_endpoint: API端点
            details: 异常详情
        """
        super().__init__(message, code="EAI_AUTH", details=details)
        self.api_endpoint = api_endpoint


class ValidationError(EnterpriseAIException):
    """数据验证错误异常

    当输入数据验证失败时抛出。
    """

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, details: Optional[dict] = None):
        """初始化验证错误

        Args:
            message: 异常消息
            field: 验证失败的字段名
            value: 验证失败的值
            details: 异常详情
        """
        super().__init__(message, code="EAI_VALIDATION", details=details)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        if self.field:
            return f"{base_str} (field: {self.field})"
        return base_str


class NetworkError(EnterpriseAIException):
    """网络错误异常

    当网络请求失败、超时或连接错误时抛出。
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None
    ):
        """初始化网络错误

        Args:
            message: 异常消息
            url: 请求URL
            status_code: HTTP状态码
            details: 异常详情
        """
        super().__init__(message, code="EAI_NETWORK", details=details)
        self.url = url
        self.status_code = status_code

    def __str__(self) -> str:
        """字符串表示"""
        base_str = super().__str__()
        parts = []
        if self.url:
            parts.append(f"url: {self.url}")
        if self.status_code:
            parts.append(f"status: {self.status_code}")
        if parts:
            return f"{base_str} ({'; '.join(parts)})"
        return base_str


from typing import Optional, Any
