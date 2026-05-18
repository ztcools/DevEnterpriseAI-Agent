# -*- coding: utf-8 -*-
"""
企业开发专用工具模块

包含5个企业开发专用工具：
1. 代码生成工具
2. 代码重构工具
3. 编译错误分析工具
4. 开发文档生成工具
5. 自动化脚本工具
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool, ToolOutputSchema, register_tool
from utils import get_logger, LLMError
from core.llm import LLMFactory, EnterpriseLLM


class CodeGeneratorInput(BaseModel):
    """代码生成工具输入Schema"""
    language: str = Field(description="目标编程语言，如python、cpp、java")
    framework: Optional[str] = Field(description="使用的框架，如django、fastapi、spring")
    functionality: str = Field(description="需要实现的功能描述")
    requirements: Optional[str] = Field(description="额外的需求和约束条件")


class CodeGeneratorOutput(ToolOutputSchema):
    """代码生成工具输出Schema"""
    code: Optional[str] = Field(default=None, description="生成的代码")
    explanation: Optional[str] = Field(default=None, description="代码说明")


@register_tool(name="code_generator")
class CodeGeneratorTool(BaseTool):
    """代码生成工具

    根据结构化参数，结合内部编码规范，生成符合公司规范的代码。
    """

    name = "code_generator"
    description = "根据功能描述和约束条件生成符合公司编码规范的代码。输入参数包括编程语言、框架、功能描述和额外需求。"
    input_schema = CodeGeneratorInput
    output_schema = CodeGeneratorOutput

    def __init__(self, llm: Optional[EnterpriseLLM] = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(self.__class__.__name__)
        
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm
        
        self._coding_standards = self._load_coding_standards()

    def _load_coding_standards(self) -> str:
        """加载内部编码规范"""
        standards = """
公司编码规范：
1. Python命名规范：
   - 模块名：全部小写，下划线分隔
   - 类名：大驼峰命名法
   - 函数/变量名：小写，下划线分隔
   - 常量名：全大写，下划线分隔

2. 代码风格：
   - 使用4空格缩进，禁止Tab
   - 每行不超过120字符
   - 二元运算符前后加空格

3. 注释规范：
   - 模块、类、函数必须有文档字符串
   - 复杂逻辑需要注释说明

4. 导入规范：
   - 按标准库、第三方库、内部库顺序排列
   - 禁止使用from module import *

5. 异常处理：
   - 禁止捕获所有异常
   - 只捕获明确需要处理的异常类型
"""
        return standards.strip()

    def _execute(self, **kwargs) -> CodeGeneratorOutput:
        """执行代码生成"""
        try:
            input_data = CodeGeneratorInput(**kwargs)
            
            prompt = f"""你是一位经验丰富的企业级开发工程师，需要根据以下要求生成代码。

【公司编码规范】
{self._coding_standards}

【生成要求】
- 编程语言：{input_data.language}
- 框架：{input_data.framework or "无"}
- 功能描述：{input_data.functionality}
- 额外需求：{input_data.requirements or "无"}

请严格按照公司编码规范生成代码，并提供代码说明。

输出格式：
```
【代码】
<生成的代码>

【说明】
<代码功能和设计说明>
```
"""

            self.logger.debug(f"Code generation prompt length: {len(prompt)}")
            
            result = self._llm.invoke(prompt)
            content = result.content

            code = ""
            explanation = ""
            
            code_start = content.find("【代码】")
            code_end = content.find("【说明】")
            
            if code_start != -1 and code_end != -1:
                code = content[code_start + 4:code_end].strip()
                explanation = content[code_end + 4:].strip()
            else:
                code = content
                explanation = "代码已生成，请参考代码注释"

            return CodeGeneratorOutput(
                success=True,
                result=f"代码生成成功\n\n【代码】\n{code}\n\n【说明】\n{explanation}",
                code=code,
                explanation=explanation
            )

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return CodeGeneratorOutput(
                success=False,
                error=str(e)
            )


class CodeRefactorInput(BaseModel):
    """代码重构工具输入Schema"""
    code: str = Field(description="需要重构的原始代码")
    language: str = Field(description="代码编程语言")
    refactor_type: Optional[str] = Field(description="重构类型：performance（性能优化）、readability（可读性）、maintainability（可维护性）、security（安全性）")
    requirements: Optional[str] = Field(description="重构要求")


class CodeRefactorOutput(ToolOutputSchema):
    """代码重构工具输出Schema"""
    refactored_code: Optional[str] = Field(default=None, description="重构后的代码")
    changes: Optional[List[str]] = Field(default=None, description="修改点列表")


@register_tool(name="code_refactor")
class CodeRefactorTool(BaseTool):
    """代码重构工具

    优化代码结构、降低耦合、保持功能不变。
    """

    name = "code_refactor"
    description = "对现有代码进行重构优化，包括性能优化、可读性提升、可维护性改进等。输入参数包括原始代码、编程语言、重构类型和额外要求。"
    input_schema = CodeRefactorInput
    output_schema = CodeRefactorOutput

    def __init__(self, llm: Optional[EnterpriseLLM] = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(self.__class__.__name__)
        
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm

    def _execute(self, **kwargs) -> CodeRefactorOutput:
        """执行代码重构"""
        try:
            input_data = CodeRefactorInput(**kwargs)
            
            refactor_types = {
                "performance": "性能优化：减少时间复杂度、优化算法、减少内存使用",
                "readability": "可读性提升：清晰命名、适当注释、代码结构优化",
                "maintainability": "可维护性改进：降低耦合、提高内聚、模块化设计",
                "security": "安全性增强：防止注入攻击、验证输入、安全编码"
            }
            
            refactor_desc = refactor_types.get(input_data.refactor_type, "综合性重构")
            
            prompt = f"""你是一位资深代码重构专家，请对以下代码进行重构。

【重构目标】
{refactor_desc}

【原始代码】
{input_data.code}

【编程语言】
{input_data.language}

【额外要求】
{input_data.requirements or "无"}

【重构原则】
1. 保持功能不变
2. 降低代码耦合度
3. 提高代码可读性
4. 遵循SOLID原则
5. 添加必要的注释说明

请输出重构后的代码和修改说明。

输出格式：
```
【重构后代码】
<重构后的代码>

【修改说明】
1. <修改点1>
2. <修改点2>
3. <修改点3>
```
"""

            self.logger.debug(f"Code refactor prompt length: {len(prompt)}")
            
            result = self._llm.invoke(prompt)
            content = result.content

            refactored_code = ""
            changes = []
            
            code_start = content.find("【重构后代码】")
            changes_start = content.find("【修改说明】")
            
            if code_start != -1 and changes_start != -1:
                refactored_code = content[code_start + 6:changes_start].strip()
                changes_text = content[changes_start + 6:].strip()
                changes = [line.strip("- ").strip() for line in changes_text.split('\n') if line.strip()]
            else:
                refactored_code = content
                changes = ["代码已重构"]

            return CodeRefactorOutput(
                success=True,
                result=f"代码重构完成\n\n【重构后代码】\n{refactored_code}\n\n【修改说明】\n{chr(10).join(changes)}",
                refactored_code=refactored_code,
                changes=changes
            )

        except Exception as e:
            self.logger.error(f"Code refactoring failed: {e}")
            return CodeRefactorOutput(
                success=False,
                error=str(e)
            )


class CompileErrorAnalyzeInput(BaseModel):
    """编译错误分析工具输入Schema"""
    error_log: str = Field(description="编译错误日志内容")
    language: Optional[str] = Field(description="编程语言，如cpp、python、java")
    build_system: Optional[str] = Field(description="构建系统，如cmake、make、maven")


class CompileErrorAnalyzeOutput(ToolOutputSchema):
    """编译错误分析工具输出Schema"""
    error_type: Optional[str] = Field(default=None, description="错误类型")
    error_location: Optional[str] = Field(default=None, description="错误位置")
    solution: Optional[str] = Field(default=None, description="修复方案")
    suggestions: Optional[List[str]] = Field(default=None, description="建议列表")


@register_tool(name="compile_error_analyzer")
class CompileErrorAnalyzerTool(BaseTool):
    """编译错误分析工具

    解析编译日志，结合内部知识库返回企业修复方案。
    """

    name = "compile_error_analyzer"
    description = "分析编译错误日志，识别错误类型并提供符合公司规范的修复方案。输入参数包括错误日志、编程语言和构建系统。"
    input_schema = CompileErrorAnalyzeInput
    output_schema = CompileErrorAnalyzeOutput

    def __init__(self, llm: Optional[EnterpriseLLM] = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(self.__class__.__name__)
        
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm
        
        self._error_solutions = self._load_error_solutions()

    def _load_error_solutions(self) -> str:
        """加载内部错误解决方案知识库"""
        solutions = """
公司编译错误解决方案知识库：

【链接错误】
1. undefined reference to `xxx`:
   - 检查头文件是否正确包含
   - 确认源文件已添加到CMakeLists.txt
   - 检查链接库顺序

2. cannot find -lxxx:
   - 使用find_package()查找库
   - 检查LD_LIBRARY_PATH环境变量
   - 确认库已正确安装

【编译错误】
1. ‘xxx’ was not declared in this scope:
   - 添加缺失的头文件
   - 检查命名空间是否正确
   - 确认前向声明

2. invalid use of incomplete type:
   - 添加头文件包含
   - 检查前向声明是否正确

【CMake错误】
1. Could NOT find xxx:
   - 安装缺失的依赖包
   - 设置正确的环境变量
   - 检查Findxxx.cmake路径

2. CMake Error at CMakeLists.txt:
   - 删除build目录重新构建
   - 检查CMakeLists.txt语法

【运行时错误】
1. error while loading shared libraries:
   - 设置LD_LIBRARY_PATH环境变量
   - 将库安装到系统路径
"""
        return solutions.strip()

    def _execute(self, **kwargs) -> CompileErrorAnalyzeOutput:
        """执行编译错误分析"""
        try:
            input_data = CompileErrorAnalyzeInput(**kwargs)
            
            prompt = f"""你是一位经验丰富的编译工程师，请分析以下编译错误并提供解决方案。

【内部知识库】
{self._error_solutions}

【错误日志】
{input_data.error_log}

【编程语言】
{input_data.language or "未知"}

【构建系统】
{input_data.build_system or "未知"}

请按照以下格式输出分析结果：

【错误类型】
<错误类型描述>

【错误位置】
<文件路径和行号>

【修复方案】
<详细的修复步骤>

【建议】
1. <建议1>
2. <建议2>
"""

            self.logger.debug(f"Error analysis prompt length: {len(prompt)}")
            
            result = self._llm.invoke(prompt)
            content = result.content

            error_type = ""
            error_location = ""
            solution = ""
            suggestions = []
            
            sections = content.split("【")
            for section in sections:
                if section.startswith("错误类型】"):
                    error_type = section[4:].split("【")[0].strip()
                elif section.startswith("错误位置】"):
                    error_location = section[4:].split("【")[0].strip()
                elif section.startswith("修复方案】"):
                    solution = section[4:].split("【")[0].strip()
                elif section.startswith("建议】"):
                    suggestions_text = section[3:].split("【")[0].strip()
                    suggestions = [line.strip("- ").strip() for line in suggestions_text.split('\n') if line.strip()]

            return CompileErrorAnalyzeOutput(
                success=True,
                result=f"错误分析完成\n\n【错误类型】{error_type}\n\n【错误位置】{error_location}\n\n【修复方案】{solution}\n\n【建议】\n{chr(10).join(suggestions)}",
                error_type=error_type,
                error_location=error_location,
                solution=solution,
                suggestions=suggestions
            )

        except Exception as e:
            self.logger.error(f"Error analysis failed: {e}")
            return CompileErrorAnalyzeOutput(
                success=False,
                error=str(e)
            )


class DocGeneratorInput(BaseModel):
    """文档生成工具输入Schema"""
    code: str = Field(description="需要生成文档的代码")
    language: str = Field(description="代码编程语言")
    doc_type: Optional[str] = Field(description="文档类型：api（接口文档）、class（类文档）、function（函数文档）、readme（项目说明）")
    format: Optional[str] = Field(description="输出格式：markdown、rst")


class DocGeneratorOutput(ToolOutputSchema):
    """文档生成工具输出Schema"""
    documentation: Optional[str] = Field(default=None, description="生成的文档内容")
    doc_type: Optional[str] = Field(default=None, description="文档类型")


@register_tool(name="doc_generator")
class DocGeneratorTool(BaseTool):
    """开发文档生成工具

    根据代码生成公司格式注释、接口文档。
    """

    name = "doc_generator"
    description = "根据代码生成符合公司格式的文档，包括接口文档、类文档、函数文档等。输入参数包括代码内容、编程语言、文档类型和输出格式。"
    input_schema = DocGeneratorInput
    output_schema = DocGeneratorOutput

    def __init__(self, llm: Optional[EnterpriseLLM] = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(self.__class__.__name__)
        
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm
        
        self._doc_templates = self._load_doc_templates()

    def _load_doc_templates(self) -> str:
        """加载公司文档模板"""
        templates = '''
公司文档格式规范：

【函数文档】
def function_name(param1: type, param2: type) -> return_type:
    \"\"\"函数功能描述
    
    Args:
        param1: 参数说明
        param2: 参数说明
    
    Returns:
        返回值说明
    
    Raises:
        异常类型: 异常说明
    \"\"\"

【类文档】
class ClassName:
    \"\"\"类功能描述
    
    属性:
        attribute1: 属性说明
    
    方法:
        method1: 方法说明
    \"\"\"

【接口文档】
## API接口文档

### 接口路径
/api/v1/endpoint

### HTTP方法
GET/POST/PUT/DELETE

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| param1 | string | 是 | 参数说明 |

### 响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

【README文档】
# 项目名称

## 项目简介
项目功能描述

## 技术栈
- Python 3.10+
- FastAPI
- SQLite

## 快速开始
```bash
pip install -r requirements.txt
python main.py
```
'''
        return templates.strip()

    def _execute(self, **kwargs) -> DocGeneratorOutput:
        """执行文档生成"""
        try:
            input_data = DocGeneratorInput(**kwargs)
            
            doc_type_desc = {
                "api": "API接口文档",
                "class": "类文档",
                "function": "函数/方法文档",
                "readme": "项目README文档"
            }
            
            doc_format = input_data.format or "markdown"
            
            prompt = f"""你是一位专业的技术文档工程师，请根据以下代码生成符合公司规范的文档。

【公司文档格式规范】
{self._doc_templates}

【待文档化代码】
{input_data.code}

【编程语言】
{input_data.language}

【文档类型】
{doc_type_desc.get(input_data.doc_type, "综合文档")}

【输出格式】
{doc_format}

请输出完整的文档内容。
"""

            self.logger.debug(f"Doc generation prompt length: {len(prompt)}")
            
            result = self._llm.invoke(prompt)
            content = result.content

            return DocGeneratorOutput(
                success=True,
                result=f"文档生成成功\n\n{content}",
                documentation=content,
                doc_type=input_data.doc_type
            )

        except Exception as e:
            self.logger.error(f"Doc generation failed: {e}")
            return DocGeneratorOutput(
                success=False,
                error=str(e)
            )


class ScriptGeneratorInput(BaseModel):
    """脚本生成工具输入Schema"""
    script_type: str = Field(description="脚本类型：build（编译脚本）、deploy（部署脚本）、test（测试脚本）、ci（CI配置）")
    language: Optional[str] = Field(description="目标语言/框架")
    requirements: Optional[str] = Field(description="脚本需求描述")


class ScriptGeneratorOutput(ToolOutputSchema):
    """脚本生成工具输出Schema"""
    script: Optional[str] = Field(default=None, description="生成的脚本内容")
    script_type: Optional[str] = Field(default=None, description="脚本类型")


@register_tool(name="script_generator")
class ScriptGeneratorTool(BaseTool):
    """自动化脚本工具

    生成内部编译、打包、CI简易脚本。
    """

    name = "script_generator"
    description = "生成企业内部使用的自动化脚本，包括编译脚本、部署脚本、测试脚本和CI配置。输入参数包括脚本类型、目标语言和额外需求。"
    input_schema = ScriptGeneratorInput
    output_schema = ScriptGeneratorOutput

    def __init__(self, llm: Optional[EnterpriseLLM] = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(self.__class__.__name__)
        
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm
        
        self._script_templates = self._load_script_templates()

    def _load_script_templates(self) -> str:
        """加载公司脚本模板"""
        templates = """
公司脚本规范：

【CMake编译脚本】
#!/bin/bash
set -e

mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
make install

【Python打包脚本】
#!/bin/bash
set -e

pip install -r requirements.txt
python setup.py sdist bdist_wheel
twine upload dist/*

【Docker部署脚本】
#!/bin/bash
set -e

IMAGE_NAME="myapp:latest"

docker build -t $IMAGE_NAME .
docker tag $IMAGE_NAME registry.example.com/$IMAGE_NAME
docker push registry.example.com/$IMAGE_NAME

【CI配置（GitHub Actions）】
name: CI

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: pytest

【单元测试脚本】
#!/bin/bash
set -e

cd tests
python -m pytest -v
python -m pytest --cov=src
"""
        return templates.strip()

    def _execute(self, **kwargs) -> ScriptGeneratorOutput:
        """执行脚本生成"""
        try:
            input_data = ScriptGeneratorInput(**kwargs)
            
            script_type_desc = {
                "build": "编译构建脚本",
                "deploy": "部署脚本",
                "test": "测试脚本",
                "ci": "CI/CD配置脚本"
            }
            
            prompt = f"""你是一位DevOps工程师，请根据以下要求生成自动化脚本。

【公司脚本规范】
{self._script_templates}

【脚本类型】
{script_type_desc.get(input_data.script_type, "通用脚本")}

【目标语言/框架】
{input_data.language or "通用"}

【需求描述】
{input_data.requirements or "无"}

请输出完整的脚本内容，并添加必要的注释说明。
"""

            self.logger.debug(f"Script generation prompt length: {len(prompt)}")
            
            result = self._llm.invoke(prompt)
            content = result.content

            return ScriptGeneratorOutput(
                success=True,
                result=f"脚本生成成功\n\n{content}",
                script=content,
                script_type=input_data.script_type
            )

        except Exception as e:
            self.logger.error(f"Script generation failed: {e}")
            return ScriptGeneratorOutput(
                success=False,
                error=str(e)
            )