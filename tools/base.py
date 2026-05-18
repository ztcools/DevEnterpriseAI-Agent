# -*- coding: utf-8 -*-
"""
自定义工具基类模块

提供Agent自定义工具的抽象基类和工具注册机制。
所有自定义工具需继承BaseTool基类并实现相应接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type
from pydantic import BaseModel, Field


class ToolInputSchema(BaseModel):
    """工具输入参数Schema"""
    pass


class ToolOutputSchema(BaseModel):
    """工具输出结果Schema"""
    success: bool = Field(default=True, description="执行是否成功")
    result: Any = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")


class BaseTool(ABC):
    """自定义工具抽象基类

    所有Agent工具需继承此类并实现以下属性和方法：
    - name: 工具名称（唯一标识）
    - description: 工具描述（用于LLM理解工具用途）
    - input_schema: 输入参数Schema
    - output_schema: 输出结果Schema
    - _execute: 实际执行逻辑
    """

    name: str = ""
    description: str = ""
    input_schema: Type[ToolInputSchema] = ToolInputSchema
    output_schema: Type[ToolOutputSchema] = ToolOutputSchema

    def __init__(self, **kwargs: Any):
        """初始化工具实例"""
        self._config = kwargs
        self._validate_config()

    def _validate_config(self) -> None:
        """验证配置参数"""
        pass

    @abstractmethod
    def _execute(self, **kwargs: Any) -> ToolOutputSchema:
        """工具实际执行逻辑

        Args:
            **kwargs: 工具输入参数

        Returns:
            ToolOutputSchema: 执行结果
        """
        pass

    def run(self, input_data: Dict[str, Any]) -> ToolOutputSchema:
        """工具执行入口

        Args:
            input_data: 输入参数字典

        Returns:
            ToolOutputSchema: 执行结果
        """
        try:
            result = self._execute(**input_data)
            if not isinstance(result, ToolOutputSchema):
                result = ToolOutputSchema(success=True, result=result)
            return result
        except Exception as e:
            return ToolOutputSchema(success=False, result=None, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema定义

        Returns:
            Dict[str, Any]: 工具Schema字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema() if hasattr(self.input_schema, 'model_json_schema') else {},
            "output": self.output_schema.model_json_schema() if hasattr(self.output_schema, 'model_json_schema') else {}
        }


class ToolRegistry:
    """工具注册器

    提供工具的注册、获取和列表功能。
    """

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}

    def register(self, tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """注册工具类

        Args:
            tool_class: 工具类
            name: 工具名称，默认使用类属性name
        """
        tool_name = name or tool_class.name
        if not tool_name:
            raise ValueError(f"Tool class {tool_class.__name__} must have a name attribute")
        self._tools[tool_name] = tool_class

    def get(self, name: str) -> Optional[Type[BaseTool]]:
        """获取工具类

        Args:
            name: 工具名称

        Returns:
            Optional[Type[BaseTool]]: 工具类，未找到返回None
        """
        return self._tools.get(name)

    def create(self, name: str, **kwargs: Any) -> Optional[BaseTool]:
        """创建工具实例

        Args:
            name: 工具名称
            **kwargs: 工具初始化参数

        Returns:
            Optional[BaseTool]: 工具实例，未找到返回None
        """
        tool_class = self.get(name)
        if tool_class is None:
            return None
        return tool_class(**kwargs)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册工具

        Returns:
            Dict[str, Dict[str, Any]]: 工具名称到Schema的映射
        """
        result = {}
        for name, tool_class in self._tools.items():
            tool_instance = tool_class()
            result[name] = tool_instance.get_schema()
        return result

    def clear(self) -> None:
        """清空所有已注册工具"""
        self._tools.clear()


_global_registry = ToolRegistry()


def register_tool(name: Optional[str] = None) -> Callable:
    """工具注册装饰器

    Args:
        name: 工具名称，默认使用类属性name

    Returns:
        Callable: 装饰器函数
    """
    def decorator(tool_class: Type[BaseTool]) -> Type[BaseTool]:
        _global_registry.register(tool_class, name)
        return tool_class
    return decorator


class ToolFactory:
    """工具工厂类

    提供工具的创建和管理功能。
    """

    @staticmethod
    def get_registry() -> ToolRegistry:
        """获取全局工具注册器

        Returns:
            ToolRegistry: 工具注册器实例
        """
        return _global_registry

    @staticmethod
    def register_tool(tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """注册工具类

        Args:
            tool_class: 工具类
            name: 工具名称
        """
        _global_registry.register(tool_class, name)

    @staticmethod
    def create_tool(name: str, **kwargs: Any) -> Optional[BaseTool]:
        """创建工具实例

        Args:
            name: 工具名称
            **kwargs: 工具初始化参数

        Returns:
            Optional[BaseTool]: 工具实例
        """
        return _global_registry.create(name, **kwargs)

    @staticmethod
    def list_all_tools() -> Dict[str, Dict[str, Any]]:
        """列出所有已注册工具

        Returns:
            Dict[str, Dict[str, Any]]: 工具字典
        """
        return _global_registry.list_tools()

    @staticmethod
    def get_tool_schema(name: str) -> Optional[Dict[str, Any]]:
        """获取指定工具的Schema

        Args:
            name: 工具名称

        Returns:
            Optional[Dict[str, Any]]: 工具Schema
        """
        tool_class = _global_registry.get(name)
        if tool_class is None:
            return None
        tool_instance = tool_class()
        return tool_instance.get_schema()
