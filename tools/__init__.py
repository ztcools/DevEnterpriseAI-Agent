# -*- coding: utf-8 -*-
"""
工具模块初始化文件

注册所有企业开发专用工具。
"""

from .base import BaseTool, ToolFactory, register_tool, ToolInputSchema, ToolOutputSchema
from .enterprise_tools import (
    CodeGeneratorTool,
    CodeRefactorTool,
    CompileErrorAnalyzerTool,
    DocGeneratorTool,
    ScriptGeneratorTool,
    CodeGeneratorInput,
    CodeGeneratorOutput,
    CodeRefactorInput,
    CodeRefactorOutput,
    CompileErrorAnalyzeInput,
    CompileErrorAnalyzeOutput,
    DocGeneratorInput,
    DocGeneratorOutput,
    ScriptGeneratorInput,
    ScriptGeneratorOutput,
)

__all__ = [
    "BaseTool",
    "ToolFactory",
    "register_tool",
    "ToolInputSchema",
    "ToolOutputSchema",
    "CodeGeneratorTool",
    "CodeRefactorTool",
    "CompileErrorAnalyzerTool",
    "DocGeneratorTool",
    "ScriptGeneratorTool",
    "CodeGeneratorInput",
    "CodeGeneratorOutput",
    "CodeRefactorInput",
    "CodeRefactorOutput",
    "CompileErrorAnalyzeInput",
    "CompileErrorAnalyzeOutput",
    "DocGeneratorInput",
    "DocGeneratorOutput",
    "ScriptGeneratorInput",
    "ScriptGeneratorOutput",
]

# 自动注册所有工具
def _register_tools():
    """注册所有企业工具"""
    tools = [
        CodeGeneratorTool,
        CodeRefactorTool,
        CompileErrorAnalyzerTool,
        DocGeneratorTool,
        ScriptGeneratorTool,
    ]
    for tool in tools:
        ToolFactory.register_tool(tool)


_register_tools()