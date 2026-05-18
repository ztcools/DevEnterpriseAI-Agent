# -*- coding: utf-8 -*-
"""
大语言模型核心接口模块

提供统一的LLM接口封装，支持私有化大模型部署，兼容OpenAI接口格式。
支持多种大模型的接入，包括OpenAI GPT、国产大模型（文心、通义、智谱等）。
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Union
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from config import get_settings


class BaseLLM(ABC):
    """大语言模型抽象基类"""

    @abstractmethod
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
        """
        pass

    @abstractmethod
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
        """
        pass


class EnterpriseLLM(BaseLLM):
    """企业级大语言模型封装类

    适配私有化大模型，支持国产大模型接口调用。
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

        self._client: Optional[ChatOpenAI] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI兼容客户端"""
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
        """
        if self._client is None:
            self._init_client()
        return self._client.generate(messages, **kwargs)

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
        """
        if self._client is None:
            self._init_client()
        return self._client.stream(messages, **kwargs)

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

        self._client: Optional[OpenAIEmbeddings] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI兼容嵌入客户端"""
        self._client = OpenAIEmbeddings(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model_name,
            **self.extra_params
        )

    def embed_query(self, text: str) -> List[float]:
        """单个文本向量化

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量结果
        """
        if self._client is None:
            self._init_client()
        return self._client.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化

        Args:
            texts: 待向量化的文本列表

        Returns:
            List[List[float]]: 向量结果列表
        """
        if self._client is None:
            self._init_client()
        return self._client.embed_documents(texts)

    def embed_image(self, image_path: str) -> List[float]:
        """图像向量化（需要视觉模型支持）

        Args:
            image_path: 图像路径

        Returns:
            List[float]: 向量结果
        """
        raise NotImplementedError("Image embedding requires vision model support")


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
            }
            for msg in history_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                msg_class = role_map.get(role, HumanMessage)
                messages.append(msg_class(content=content))

        if user_message:
            messages.append(HumanMessage(content=user_message))

        if assistant_message:
            messages.append(AIMessage(content=assistant_message))

        return messages
