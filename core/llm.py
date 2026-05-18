# -*- coding: utf-8 -*-
"""
大语言模型核心接口模块

提供统一的LLM接口封装，支持私有化大模型部署，兼容OpenAI接口格式。
包含完整的日志记录、异常捕获和性能监控功能。
"""

import time
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import (
    BaseMessage, AIMessage, HumanMessage, SystemMessage, FunctionMessage
)
from langchain_core.outputs import ChatGeneration, ChatResult

from config import get_settings
from utils import get_logger, LLMError, NetworkError, ValidationError


class BaseLLM(ABC):
    """大语言模型抽象基类"""

    @abstractmethod
    def generate(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> ChatResult:
        """生成对话内容"""
        pass

    @abstractmethod
    def stream(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> Iterator[ChatGeneration]:
        """流式生成对话内容"""
        pass


class LLMMonitor:
    """LLM调用监控器

    负责记录每次模型调用的耗时、入参、出参等信息。
    """

    def __init__(self, logger_name: str = "LLM"):
        self.logger = get_logger(logger_name)

    def log_request(
        self,
        model_name: str,
        messages: List[BaseMessage],
        params: Dict[str, Any],
        start_time: float
    ) -> None:
        """记录请求信息"""
        messages_summary = []
        total_tokens = 0
        for msg in messages:
            msg_dict = {
                "role": self._get_role(msg),
                "content_length": len(msg.content) if hasattr(msg, 'content') else 0
            }
            messages_summary.append(msg_dict)
            total_tokens += len(msg.content) // 4  # 粗略估算token数

        log_data = {
            "event": "llm_request_start",
            "model": model_name,
            "timestamp": start_time,
            "num_messages": len(messages),
            "total_content_length": total_tokens,
            "parameters": params
        }
        self.logger.info(f"LLM Request: {json.dumps(log_data, ensure_ascii=False)}")

    def log_response(
        self,
        model_name: str,
        response: ChatResult,
        duration: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """记录响应信息"""
        response_text = ""
        if response and response.generations:
            response_text = str(response.generations[0].message.content)

        log_data = {
            "event": "llm_request_end",
            "model": model_name,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "response_length": len(response_text),
            "error": error_message
        }
        if success:
            self.logger.info(f"LLM Response: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.error(f"LLM Error: {json.dumps(log_data, ensure_ascii=False)}")

    def _get_role(self, msg: BaseMessage) -> str:
        """获取消息角色"""
        if isinstance(msg, HumanMessage):
            return "user"
        elif isinstance(msg, AIMessage):
            return "assistant"
        elif isinstance(msg, SystemMessage):
            return "system"
        elif isinstance(msg, FunctionMessage):
            return "function"
        return "unknown"


class EnterpriseLLM(BaseLLM):
    """企业级大语言模型封装类

    适配私有化大模型，支持国产大模型接口调用。
    包含完整的日志记录、异常捕获和性能监控功能。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        streaming: bool = False,
        **kwargs: Any
    ):
        """初始化企业级LLM

        Args:
            api_key: API密钥，默认从配置读取
            base_url: API地址，默认从配置读取
            model_name: 模型名称，默认从配置读取
            temperature: 温度参数，默认从配置读取
            max_tokens: 最大token数，默认从配置读取
            timeout: 超时时间，默认从配置读取
            streaming: 是否流式输出，默认从配置读取
            **kwargs: 其他参数
        """
        settings = get_settings()

        self.api_key = api_key or settings.llm.api_key
        self.base_url = base_url or settings.llm.base_url
        self.model_name = model_name or settings.llm.model_name
        self.temperature = temperature if temperature is not None else settings.llm.temperature
        self.max_tokens = max_tokens or settings.llm.max_tokens
        self.timeout = timeout or settings.llm.timeout
        self.streaming = streaming
        self.extra_params = kwargs

        self.logger = get_logger(self.__class__.__name__)
        self.monitor = LLMMonitor()

        self._client: Optional[ChatOpenAI] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI兼容客户端"""
        try:
            self._client = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                streaming=self.streaming,
                **self.extra_params
            )
            self.logger.info(f"LLM client initialized: model={self.model_name}, base_url={self.base_url}")
        except Exception as e:
            raise LLMError(
                message=f"Failed to initialize LLM client: {str(e)}",
                model_name=self.model_name,
                error_type="client_init",
                details={"base_url": self.base_url}
            )

    def _validate_messages(self, messages: List[BaseMessage]) -> None:
        """验证消息格式"""
        if not isinstance(messages, list):
            raise ValidationError(
                message="Messages must be a list",
                field="messages",
                value=str(type(messages))
            )

        for i, msg in enumerate(messages):
            if not isinstance(msg, BaseMessage):
                raise ValidationError(
                    message=f"Message at index {i} must be a BaseMessage instance",
                    field="messages",
                    value=str(type(msg))
                )

    def generate(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> ChatResult:
        """生成对话内容

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            ChatResult: 生成结果

        Raises:
            ValidationError: 参数验证失败
            NetworkError: 网络请求失败
            LLMError: 模型调用失败
        """
        start_time = time.time()

        try:
            self._validate_messages(messages)

            params = {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "streaming": self.streaming,
                **kwargs
            }

            self.monitor.log_request(self.model_name, messages, params, start_time)

            if self._client is None:
                self._init_client()

            response = self._client.generate(messages, **kwargs)
            duration = time.time() - start_time

            self.monitor.log_response(self.model_name, response, duration, success=True)
            return response

        except ValidationError as e:
            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=str(e))
            raise

        except Exception as e:
            duration = time.time() - start_time

            error_type = "unknown"
            error_msg = str(e)

            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_type = "timeout"
                raise NetworkError(
                    message=f"LLM request timed out: {error_msg}",
                    url=self.base_url,
                    details={"timeout": self.timeout}
                )
            elif "connection" in error_msg.lower():
                error_type = "connection"
                raise NetworkError(
                    message=f"LLM connection error: {error_msg}",
                    url=self.base_url
                )
            elif "api_key" in error_msg.lower() or "auth" in error_msg.lower():
                error_type = "authentication"
                raise LLMError(
                    message=f"LLM authentication failed: {error_msg}",
                    model_name=self.model_name,
                    error_type="authentication"
                )
            else:
                error_type = "api_error"

            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=error_msg)

            raise LLMError(
                message=f"LLM request failed: {error_msg}",
                model_name=self.model_name,
                error_type=error_type,
                details={"exception_type": type(e).__name__}
            )

    def stream(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> Iterator[ChatGeneration]:
        """流式生成对话内容

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            ChatGeneration: 生成结果块

        Raises:
            ValidationError: 参数验证失败
            NetworkError: 网络请求失败
            LLMError: 模型调用失败
        """
        start_time = time.time()

        try:
            self._validate_messages(messages)

            params = {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "streaming": True,
                **kwargs
            }

            self.monitor.log_request(self.model_name, messages, params, start_time)

            if self._client is None:
                self._init_client()

            full_response = ChatResult(generations=[])
            response_text = ""

            for chunk in self._client.stream(messages, **kwargs):
                response_text += str(chunk.text) if hasattr(chunk, 'text') else ""
                yield chunk

            full_response.generations.append(
                ChatGeneration(message=AIMessage(content=response_text))
            )

            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, full_response, duration, success=True)

        except ValidationError as e:
            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=str(e))
            raise

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            error_type = "unknown"
            if "timeout" in error_msg.lower():
                error_type = "timeout"
                raise NetworkError(
                    message=f"LLM stream timed out: {error_msg}",
                    url=self.base_url
                )
            elif "connection" in error_msg.lower():
                error_type = "connection"
                raise NetworkError(
                    message=f"LLM stream connection error: {error_msg}",
                    url=self.base_url
                )

            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=error_msg)

            raise LLMError(
                message=f"LLM stream failed: {error_msg}",
                model_name=self.model_name,
                error_type=error_type
            )

    def invoke(
        self,
        input: Union[str, List[BaseMessage]],
        **kwargs: Any
    ) -> BaseMessage:
        """同步调用LLM

        Args:
            input: 输入字符串或消息列表
            **kwargs: 其他参数

        Returns:
            BaseMessage: 生成的响应消息
        """
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        else:
            messages = input

        result = self.generate(messages, **kwargs)
        return result.generations[0].message

    def batch(self, inputs: List[Union[str, List[BaseMessage]]], **kwargs: Any) -> List[BaseMessage]:
        """批量调用LLM

        Args:
            inputs: 输入列表
            **kwargs: 其他参数

        Returns:
            List[BaseMessage]: 响应消息列表
        """
        return [self.invoke(inp, **kwargs) for inp in inputs]

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
        """OpenAI风格的聊天补全接口

        Args:
            messages: 消息列表，格式为[{"role": "...", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: OpenAI格式的响应
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))

        result = self.invoke(langchain_messages, **kwargs)

        return {
            "id": f"chatcmpl-{hash(str(result))}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.content
                },
                "finish_reason": "stop"
            }],
            "usage": {}
        }


class EmbeddingsClient:
    """嵌入向量模型客户端

    用于文本向量化和相似度计算。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        **kwargs: Any
    ):
        """初始化嵌入向量客户端

        Args:
            api_key: API密钥，默认从配置读取
            base_url: API地址，默认从配置读取
            model_name: 模型名称，默认从配置读取
            embedding_dimension: 向量维度，默认从配置读取
            **kwargs: 其他参数
        """
        settings = get_settings()

        self.api_key = api_key or settings.llm.api_key
        self.base_url = base_url or settings.llm.base_url
        self.model_name = model_name or settings.vectorstore.embedding_model
        self.embedding_dimension = embedding_dimension or settings.vectorstore.embedding_dimension
        self.extra_params = kwargs

        self.logger = get_logger(self.__class__.__name__)
        self.monitor = LLMMonitor("Embeddings")

        self._client: Optional[OpenAIEmbeddings] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI兼容嵌入客户端"""
        try:
            self._client = OpenAIEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model_name,
                **self.extra_params
            )
            self.logger.info(f"Embeddings client initialized: model={self.model_name}")
        except Exception as e:
            raise LLMError(
                message=f"Failed to initialize embeddings client: {str(e)}",
                model_name=self.model_name,
                error_type="client_init"
            )

    def embed_query(self, text: str) -> List[float]:
        """单个文本向量化

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量结果
        """
        start_time = time.time()
        try:
            if self._client is None:
                self._init_client()

            result = self._client.embed_query(text)

            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=True)

            return result
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=str(e))
            raise LLMError(
                message=f"Embedding query failed: {str(e)}",
                model_name=self.model_name,
                error_type="embedding_error"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化

        Args:
            texts: 待向量化的文本列表

        Returns:
            List[List[float]]: 向量结果列表
        """
        start_time = time.time()
        try:
            if self._client is None:
                self._init_client()

            result = self._client.embed_documents(texts)

            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=True)

            return result
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.log_response(self.model_name, ChatResult(generations=[]), duration, success=False, error_message=str(e))
            raise LLMError(
                message=f"Embedding documents failed: {str(e)}",
                model_name=self.model_name,
                error_type="embedding_error"
            )


class LLMFactory:
    """LLM工厂类

    提供统一的LLM和嵌入模型创建接口。
    """

    @staticmethod
    def create_llm(
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        streaming: bool = False,
        **kwargs: Any
    ) -> EnterpriseLLM:
        """创建企业级LLM实例

        Args:
            api_key: API密钥
            base_url: API地址
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间
            streaming: 是否流式输出
            **kwargs: 其他参数

        Returns:
            EnterpriseLLM: LLM实例
        """
        return EnterpriseLLM(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            streaming=streaming,
            **kwargs
        )

    @staticmethod
    def create_embeddings(
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        **kwargs: Any
    ) -> EmbeddingsClient:
        """创建嵌入向量客户端实例

        Args:
            api_key: API密钥
            base_url: API地址
            model_name: 模型名称
            embedding_dimension: 向量维度
            **kwargs: 其他参数

        Returns:
            EmbeddingsClient: 嵌入客户端实例
        """
        return EmbeddingsClient(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            embedding_dimension=embedding_dimension,
            **kwargs
        )

    @staticmethod
    def create_chat_messages(
        system_message: Optional[str] = None,
        user_message: Optional[str] = None,
        assistant_message: Optional[str] = None,
        history_messages: Optional[List[Dict[str, str]]] = None
    ) -> List[BaseMessage]:
        """创建聊天消息列表

        Args:
            system_message: 系统消息
            user_message: 用户消息
            assistant_message: 助手消息
            history_messages: 历史消息列表，格式为 [{"role": "user", "content": "..."}]

        Returns:
            List[BaseMessage]: 消息列表
        """
        messages: List[BaseMessage] = []

        if system_message:
            messages.append(SystemMessage(content=system_message))

        if history_messages:
            role_map = {
                "user": HumanMessage,
                "assistant": AIMessage,
                "system": SystemMessage,
                "ai": AIMessage,
                "human": HumanMessage,
                "function": FunctionMessage,
            }
            for msg in history_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                msg_class = role_map.get(role, HumanMessage)
                if msg_class == FunctionMessage:
                    messages.append(FunctionMessage(content=content, name=msg.get("name", "function")))
                else:
                    messages.append(msg_class(content=content))

        if user_message:
            messages.append(HumanMessage(content=user_message))

        if assistant_message:
            messages.append(AIMessage(content=assistant_message))

        return messages