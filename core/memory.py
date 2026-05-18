# -*- coding: utf-8 -*-
"""
会话记忆模块

提供短期会话记忆管理，支持对话历史自动压缩，防止上下文溢出。
基于LangChain的ConversationSummaryMemory实现。
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import (
    BaseMessage, AIMessage, HumanMessage, SystemMessage, get_buffer_string
)
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain.prompts import PromptTemplate

from config import get_settings
from utils import get_logger, ConfigurationError
from core.llm import EnterpriseLLM


class BaseMemory(ABC):
    """记忆管理抽象基类"""

    @abstractmethod
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        pass

    @abstractmethod
    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        pass

    @abstractmethod
    def add_ai_message(self, content: str) -> None:
        """添加AI消息"""
        pass

    @abstractmethod
    def get_history(self) -> List[BaseMessage]:
        """获取历史消息"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空记忆"""
        pass

    @abstractmethod
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """加载记忆变量"""
        pass


class ConversationMemory(BaseMemory):
    """会话记忆管理器

    支持自动压缩对话历史，防止上下文溢出。
    采用分层记忆策略：短期详细记忆 + 长期摘要记忆。
    """

    def __init__(
        self,
        llm: Optional[EnterpriseLLM] = None,
        max_history: Optional[int] = None,
        memory_key: str = "history",
        return_messages: bool = True,
        verbose: bool = False
    ):
        """初始化会话记忆

        Args:
            llm: LLM实例，用于生成对话摘要
            max_history: 最大历史消息数
            memory_key: 记忆变量名称
            return_messages: 是否返回消息对象
            verbose: 是否输出详细日志
        """
        settings = get_settings()

        self.max_history = max_history or settings.memory.max_history
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.verbose = verbose

        self.logger = get_logger(self.__class__.__name__)

        if llm is None:
            from core.llm import LLMFactory
            llm = LLMFactory.create_llm()

        self._llm = llm
        self._buffer_memory = ConversationBufferMemory(
            memory_key=memory_key,
            return_messages=return_messages,
            max_len=self.max_history
        )
        self._summary_memory = ConversationSummaryMemory(
            llm=self._llm._client,
            memory_key=memory_key,
            return_messages=return_messages
        )

        self._total_tokens = 0
        self._summary_trigger_tokens = 2048
        self._last_summary = ""
        self._history: List[BaseMessage] = []

        self.logger.info(f"ConversationMemory initialized: max_history={self.max_history}")

    def add_message(self, message: BaseMessage) -> None:
        """添加消息到记忆

        Args:
            message: 消息对象
        """
        self._history.append(message)

        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

        self._buffer_memory.chat_memory.add_message(message)
        self._summary_memory.chat_memory.add_message(message)

        self._update_total_tokens(str(message.content))
        self._check_summary_needed()

        if self.verbose:
            self.logger.debug(f"Added message: role={self._get_role(message)}, length={len(message.content)}")

    def add_user_message(self, content: str) -> None:
        """添加用户消息

        Args:
            content: 用户消息内容
        """
        message = HumanMessage(content=content)
        self.add_message(message)

    def add_ai_message(self, content: str) -> None:
        """添加AI消息

        Args:
            content: AI消息内容
        """
        message = AIMessage(content=content)
        self.add_message(message)

    def get_history(self) -> List[BaseMessage]:
        """获取历史消息

        Returns:
            List[BaseMessage]: 历史消息列表
        """
        return self._history.copy()

    def get_history_as_dict(self) -> List[Dict[str, str]]:
        """获取历史消息（字典格式）

        Returns:
            List[Dict[str, str]]: 历史消息列表
        """
        history = []
        for msg in self._history:
            history.append({
                "role": self._get_role(msg),
                "content": msg.content
            })
        return history

    def get_summary(self) -> str:
        """获取对话摘要

        Returns:
            str: 对话摘要
        """
        return self._last_summary

    def clear(self) -> None:
        """清空记忆"""
        self._history = []
        self._buffer_memory.clear()
        self._summary_memory.clear()
        self._total_tokens = 0
        self._last_summary = ""
        self.logger.info("ConversationMemory cleared")

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """加载记忆变量

        Args:
            inputs: 输入变量

        Returns:
            Dict[str, Any]: 记忆变量
        """
        if self.return_messages:
            return {self.memory_key: self._history}
        else:
            return {self.memory_key: get_buffer_string(self._history)}

    def _get_role(self, message: BaseMessage) -> str:
        """获取消息角色"""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        elif isinstance(message, SystemMessage):
            return "system"
        return "unknown"

    def _update_total_tokens(self, text: str) -> None:
        """更新总token数（粗略估算）"""
        self._total_tokens += len(text) // 4

    def _check_summary_needed(self) -> None:
        """检查是否需要生成摘要"""
        if self._total_tokens >= self._summary_trigger_tokens:
            self._generate_summary()

    def _generate_summary(self) -> None:
        """生成对话摘要"""
        try:
            if self._llm is None:
                self.logger.warning("No LLM available for summary generation")
                return

            summary = self._summary_memory.load_memory_variables({})

            if summary and self.memory_key in summary:
                self._last_summary = str(summary[self.memory_key])

                if self._last_summary:
                    self._history = [SystemMessage(content=f"对话摘要: {self._last_summary}")]
                    self._total_tokens = 0
                    self._buffer_memory.clear()

                    self.logger.info(f"Generated summary, history compressed. Summary length: {len(self._last_summary)}")

                    if self.verbose:
                        self.logger.debug(f"Summary content: {self._last_summary[:200]}...")
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {str(e)}")

    def get_memory_size(self) -> int:
        """获取记忆大小

        Returns:
            int: 历史消息数量
        """
        return len(self._history)

    def get_total_tokens(self) -> int:
        """获取总token数估算

        Returns:
            int: 总token数
        """
        return self._total_tokens

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 记忆状态字典
        """
        return {
            "history": self.get_history_as_dict(),
            "summary": self._last_summary,
            "total_tokens": self._total_tokens,
            "memory_size": self.get_memory_size()
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典恢复记忆

        Args:
            data: 记忆状态字典
        """
        self.clear()

        if "summary" in data and data["summary"]:
            self._last_summary = data["summary"]
            self._history.append(SystemMessage(content=f"对话摘要: {self._last_summary}"))

        if "history" in data:
            role_map = {
                "user": HumanMessage,
                "assistant": AIMessage,
                "system": SystemMessage,
            }
            for msg in data["history"]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                msg_class = role_map.get(role, HumanMessage)
                self._history.append(msg_class(content=content))

        if "total_tokens" in data:
            self._total_tokens = data["total_tokens"]

        self.logger.info(f"Memory restored: {len(self._history)} messages")


class MemoryFactory:
    """记忆工厂类

    提供统一的记忆管理器创建接口。
    """

    @staticmethod
    def create_memory(
        llm: Optional[EnterpriseLLM] = None,
        memory_type: Optional[str] = None,
        max_history: Optional[int] = None,
        **kwargs: Any
    ) -> ConversationMemory:
        """创建会话记忆管理器

        Args:
            llm: LLM实例
            memory_type: 记忆类型（buffer/summary）
            max_history: 最大历史消息数
            **kwargs: 其他参数

        Returns:
            ConversationMemory: 会话记忆实例
        """
        settings = get_settings()

        memory_type = memory_type or settings.memory.memory_type

        if memory_type not in ["buffer", "conversation_summary"]:
            raise ConfigurationError(
                message=f"Unsupported memory type: {memory_type}",
                config_key="memory_type"
            )

        return ConversationMemory(
            llm=llm,
            max_history=max_history or settings.memory.max_history,
            **kwargs
        )

    @staticmethod
    def create_buffer_memory(
        max_history: Optional[int] = None,
        **kwargs: Any
    ) -> ConversationMemory:
        """创建简单缓冲区记忆

        Args:
            max_history: 最大历史消息数
            **kwargs: 其他参数

        Returns:
            ConversationMemory: 会话记忆实例
        """
        return ConversationMemory(
            llm=None,
            max_history=max_history,
            **kwargs
        )

    @staticmethod
    def create_summary_memory(
        llm: EnterpriseLLM,
        max_history: Optional[int] = None,
        **kwargs: Any
    ) -> ConversationMemory:
        """创建带摘要的会话记忆

        Args:
            llm: LLM实例
            max_history: 最大历史消息数
            **kwargs: 其他参数

        Returns:
            ConversationMemory: 会话记忆实例
        """
        return ConversationMemory(
            llm=llm,
            max_history=max_history,
            **kwargs
        )