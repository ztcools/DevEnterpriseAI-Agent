# -*- coding: utf-8 -*-
"""
Agent核心调度模块

实现ReAct智能调度模式，包括：
- 手动工具路由映射
- LLM自主决策
- 多轮循环执行
- 知识库检索增强
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from tools.base import BaseTool, ToolFactory, ToolOutputSchema
from core.llm import EnterpriseLLM, LLMFactory
from core.memory import ConversationMemory, MemoryFactory
from knowledge.ingest import RAGRetriever, create_retriever
from utils import get_logger


class AgentToolCall:
    """工具调用指令结构"""
    
    def __init__(self, tool_name: str, params: Dict[str, Any]):
        self.tool_name = tool_name
        self.params = params
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentToolCall":
        return cls(
            tool_name=data.get("tool_name", ""),
            params=data.get("params", {})
        )
    
    def __repr__(self) -> str:
        return f"AgentToolCall(tool_name='{self.tool_name}', params={self.params})"


class AgentState:
    """Agent状态枚举"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    FINISHED = "finished"


class DevEnterpriseAgent:
    """企业级AI Agent核心调度器
    
    采用ReAct智能调度模式，实现：
    1. LLM自主判断用户意图
    2. LLM自主选择工具
    3. LLM自主抽取结构化参数
    4. 多轮循环执行
    5. 知识库检索增强
    """
    
    def __init__(
        self,
        llm: Optional[EnterpriseLLM] = None,
        memory: Optional[ConversationMemory] = None,
        retriever: Optional[RAGRetriever] = None,
        verbose: bool = True
    ):
        """初始化Agent
        
        Args:
            llm: 企业级LLM实例
            memory: 会话记忆实例
            retriever: 知识库检索器实例
            verbose: 是否打印详细日志
        """
        self.logger = get_logger(self.__class__.__name__)
        self.verbose = verbose
        
        # 初始化LLM
        if llm is None:
            llm = LLMFactory.create_llm()
        self._llm = llm
        
        # 初始化会话记忆
        if memory is None:
            memory = MemoryFactory.create_memory()
        self._memory = memory
        
        # 初始化知识库检索器
        if retriever is None:
            retriever = create_retriever()
        self._retriever = retriever
        
        # 手动维护工具映射字典 - 自研路由逻辑
        self._tool_registry = self._build_tool_registry()
        
        # 初始化状态
        self._state = AgentState.THINKING
        self._conversation_history: List[Dict[str, str]] = []
        
        self._log("✅ Agent初始化完成")
        self._log(f"📦 已加载工具: {list(self._tool_registry.keys())}")
    
    def _build_tool_registry(self) -> Dict[str, BaseTool]:
        """构建工具注册表 - 手动维护工具映射字典
        
        Returns:
            Dict[str, BaseTool]: 工具名字符串到工具实例的映射
        """
        registry = {}
        
        # 获取所有已注册工具
        tool_schemas = ToolFactory.list_all_tools()
        
        for tool_name in tool_schemas:
            tool_instance = ToolFactory.create_tool(tool_name)
            if tool_instance:
                registry[tool_name] = tool_instance
                self._log(f"  ├─ {tool_name}")
        
        return registry
    
    def _log(self, message: str, level: str = "info") -> None:
        """日志输出"""
        if self.verbose:
            print(message)
        getattr(self.logger, level)(message)
    
    def _retrieve_knowledge(self, query: str) -> str:
        """从知识库检索相关信息
        
        Args:
            query: 用户查询
            
        Returns:
            str: 检索到的知识内容（格式化后）
        """
        try:
            results = self._retriever.retrieve(query, k=3)
            if results:
                formatted = self._retriever.retrieve_and_format(query, k=3)
                self._log(f"🔍 知识库检索到 {len(results)} 条相关资料")
                return formatted
        except Exception as e:
            self._log(f"⚠️ 知识库检索失败: {e}", "warning")
        
        return ""
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词
        
        Returns:
            str: 系统提示词
        """
        # 获取所有工具描述
        tool_descriptions = []
        for tool_name, tool_instance in self._tool_registry.items():
            schema = tool_instance.get_schema()
            tool_descriptions.append(f"""工具名: {tool_name}
描述: {schema.get('description', '')}
参数: {json.dumps(schema.get('parameters', {}), ensure_ascii=False, indent=2)}""")
        
        tools_info = "\n\n".join(tool_descriptions)
        
        return f"""你是一位专业的企业开发AI助手，擅长解决软件开发相关问题。

【可用工具列表】
{tools_info}

【工具调用格式】
当你决定调用工具时，请输出以下JSON格式：
<function_calls>
[
  {{
    "tool_name": "<工具名称>",
    "params": {{
      "<参数名>": "<参数值>"
    }}
  }}
]
</function_calls>

【指令】
1. 仔细分析用户的问题，判断是否需要调用工具
2. 如果需要调用工具，请选择最合适的工具并正确填写参数
3. 如果已经获得足够信息可以直接回答用户，请用自然语言直接回复，不要调用工具
4. 回答时请使用中文

【注意】
- 只能调用列表中存在的工具
- 参数必须是正确的JSON格式
- 如果不需要调用工具，直接回答用户即可，不需要输出JSON格式
"""
    
    def _parse_tool_calls(self, response: str) -> Optional[List[AgentToolCall]]:
        """解析LLM返回中的工具调用指令
        
        Args:
            response: LLM返回内容
            
        Returns:
            Optional[List[AgentToolCall]]: 解析出的工具调用列表，无调用时返回None
        """
        # 查找<function_calls>标签
        start_tag = "<function_calls>"
        end_tag = "</function_calls>"
        
        start_idx = response.find(start_tag)
        end_idx = response.find(end_tag)
        
        if start_idx == -1 or end_idx == -1:
            # 没有找到工具调用标签，说明直接回答
            return None
        
        try:
            # 提取JSON内容
            json_content = response[start_idx + len(start_tag):end_idx].strip()
            calls_data = json.loads(json_content)
            
            # 解析工具调用
            tool_calls = []
            for call_data in calls_data:
                tool_call = AgentToolCall.from_dict(call_data)
                tool_calls.append(tool_call)
            
            return tool_calls
        
        except json.JSONDecodeError as e:
            self._log(f"❌ JSON解析失败: {e}", "error")
            return None
    
    def _execute_tool(self, tool_call: AgentToolCall) -> ToolOutputSchema:
        """执行工具调用
        
        Args:
            tool_call: 工具调用指令
            
        Returns:
            ToolOutputSchema: 工具执行结果
        """
        tool_name = tool_call.tool_name
        
        # 路由匹配
        if tool_name not in self._tool_registry:
            self._log(f"❌ 工具 '{tool_name}' 不存在", "error")
            return ToolOutputSchema(
                success=False,
                error=f"工具 '{tool_name}' 不存在"
            )
        
        tool_instance = self._tool_registry[tool_name]
        
        self._log(f"🔧 执行工具: {tool_name}")
        self._log(f"   参数: {json.dumps(tool_call.params, ensure_ascii=False)}")
        
        # 反射调用工具
        try:
            result = tool_instance.run(tool_call.params)
            return result
        except Exception as e:
            self._log(f"❌ 工具执行异常: {e}", "error")
            return ToolOutputSchema(
                success=False,
                error=str(e)
            )
    
    def _build_prompt(self, user_input: str, knowledge_context: str = "") -> str:
        """构建完整的LLM提示词
        
        Args:
            user_input: 用户输入
            knowledge_context: 知识库检索结果
            
        Returns:
            str: 完整提示词
        """
        # 获取对话历史
        history = self._memory.get_history()
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        
        prompt = f"""【对话历史】
{history_str}

【知识库参考】
{knowledge_context if knowledge_context else "无"}

【用户问题】
{user_input}

【你的任务】
根据对话历史和知识库参考，分析用户问题，决定：
1. 是否需要调用工具？
2. 如果需要，选择哪个工具？
3. 提取正确的参数。

请输出你的思考过程和决定。如果需要调用工具，请使用<function_calls>标签包裹JSON；如果可以直接回答，请直接输出回答内容。
"""
        
        return prompt
    
    def _is_task_complete(self, response: str) -> bool:
        """判断任务是否完成
        
        Args:
            response: LLM返回内容
            
        Returns:
            bool: 任务是否完成
        """
        # 检查是否包含工具调用标签
        if "<function_calls>" in response:
            return False
        
        # 检查是否包含完成相关关键词
        complete_keywords = ["完成", "已解决", "已处理", "答案是", "总结", "结束"]
        return any(keyword in response for keyword in complete_keywords)
    
    def run(self, user_input: str, max_iterations: int = 5) -> str:
        """执行Agent主循环
        
        Args:
            user_input: 用户输入
            max_iterations: 最大迭代次数
            
        Returns:
            str: 最终回答
        """
        self._log("\n" + "="*60)
        self._log(f"🎯 用户输入: {user_input}")
        self._log("="*60)
        
        # 步骤1: 从知识库检索相关知识
        knowledge_context = self._retrieve_knowledge(user_input)
        
        # 步骤2: 添加用户消息到记忆
        self._memory.add_message("user", user_input)
        
        # 步骤3: 多轮循环执行
        for iteration in range(max_iterations):
            self._log(f"\n🔄 第 {iteration + 1} 轮思考")
            
            # 构建提示词
            prompt = self._build_prompt(user_input, knowledge_context)
            
            # 调用LLM
            self._log("🧠 正在思考...")
            llm_response = self._llm.invoke(self._build_system_prompt() + prompt)
            response_content = llm_response.content
            
            self._log(f"💭 LLM返回: {response_content[:200]}...")
            
            # 解析工具调用
            tool_calls = self._parse_tool_calls(response_content)
            
            if tool_calls is None:
                # 没有工具调用，直接回答用户
                self._log("✅ 直接回答用户")
                
                # 添加助手消息到记忆
                self._memory.add_message("assistant", response_content)
                
                return response_content
            
            # 执行工具调用
            for tool_call in tool_calls:
                self._log(f"📞 调用工具: {tool_call.tool_name}")
                
                # 执行工具
                result = self._execute_tool(tool_call)
                
                # 记录工具执行结果
                if result.success:
                    self._log(f"✅ 工具执行成功")
                    self._log(f"   结果: {str(result.result)[:100]}...")
                else:
                    self._log(f"❌ 工具执行失败: {result.error}")
                
                # 将工具结果添加到对话历史
                tool_result_str = f"工具调用[{tool_call.tool_name}]: {'成功' if result.success else '失败'}\n结果: {str(result.result) if result.success else result.error}"
                self._memory.add_message("assistant", tool_result_str)
        
        self._log(f"⚠️ 达到最大迭代次数 {max_iterations}，任务未完成")
        return "任务执行超时，请简化问题或重新描述。"
    
    def chat(self, user_input: str) -> str:
        """简化的聊天接口
        
        Args:
            user_input: 用户输入
            
        Returns:
            str: 回答内容
        """
        return self.run(user_input)


def create_agent(
    llm: Optional[EnterpriseLLM] = None,
    memory: Optional[ConversationMemory] = None,
    retriever: Optional[RAGRetriever] = None,
    verbose: bool = True
) -> DevEnterpriseAgent:
    """创建Agent实例的工厂函数
    
    Args:
        llm: 企业级LLM实例
        memory: 会话记忆实例
        retriever: 知识库检索器实例
        verbose: 是否打印详细日志
        
    Returns:
        DevEnterpriseAgent: Agent实例
    """
    return DevEnterpriseAgent(
        llm=llm,
        memory=memory,
        retriever=retriever,
        verbose=verbose
    )