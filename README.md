# DevEnterpriseAI Agent

企业内网私有化 AI 开发助手 — ReAct Agent + 自研工具路由 + RAG 知识库 + 会话记忆。

## 解决什么

团队内部需要统一的 AI 编码助手，但要嵌入公司自己的编码规范、历史踩坑记录和编译流程，不能直接用公共 Copilot。本工具支持私有化部署，兼容 OpenAI API 格式，可对接任何本地/远端大模型。

## 技术栈

Python 3 · LangChain · Chroma 向量库 · pydantic-settings · OpenAI 兼容 API

## 功能

- **ReAct 调度**：LLM 自主判断意图，非工具场景直接对话，需要时选择工具执行
- **5 个企业工具**：代码生成（内置编码规范）· 代码重构 · 编译错误分析 · API/类文档生成 · 自动化脚本生成
- **自研工具路由**：手动维护工具映射字典，不依赖 LLM function calling，更可控
- **RAG 知识库**：Chroma 存储公司文档，检索增强生成
- **会话记忆**：对话历史自动摘要压缩，防止上下文溢出

## 运行

```bash
pip install -r requirements.txt
cp .env.example .env   # 编辑填入 API key / base_url / model
python main.py
```
