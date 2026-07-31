# DevEnterpriseAI Agent

企业内网私有化 AI 开发助手 — 嵌入公司编码规范、内部文档、历史踩坑记录和编译流程，通过自研工具路由 + RAG 知识库 + 会话记忆，为团队开发提效。

## ✨ 核心能力

| 工具 | 说明 |
|------|------|
| `code_generator` | 按公司编码规范生成代码（语言/框架/约束可配置） |
| `code_refactor` | 代码重构：性能优化 / 可读性 / 可维护性 / 安全性 |
| `compile_error_analyzer` | 编译错误分析，结合内部知识库给出修复方案 |
| `doc_generator` | 自动生成 API 文档 / 类文档 / 函数文档 / README |
| `script_generator` | 自动化脚本：编译 / 部署 / 测试 / CI 配置 |

## 🧠 架构

```
用户输入 → RAG 知识库检索 → ReAct Agent 循环
         ↓
    LLM 判断意图 → 自研工具路由 → 执行工具
         ↓
    会话记忆（自动摘要压缩）
```

- **ReAct 调度**：LLM 自主判断是否需要调用工具，非工具场景直接对话
- **自研工具路由**：手动维护工具映射字典，不依赖 LLM function calling
- **RAG 增强**：Chroma 向量库存储公司文档/编码规范/历史踩坑
- **会话记忆**：支持对话历史自动摘要压缩，防止上下文溢出

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API key / base_url / model

# 3. 准备知识库文档（可选）
# 将公司文档放入 knowledge/docs/ 目录

# 4. 启动
python main.py
```

## 📁 项目结构

```
├── main.py              # 入口 + 交互式 CLI
├── config/settings.py   # 全局配置（pydantic-settings，.env 加载）
├── core/
│   ├── agent.py         # ReAct Agent 调度器
│   ├── llm.py           # LLM 封装（兼容 OpenAI API 格式）
│   └── memory.py        # 会话记忆 + 自动摘要
├── tools/
│   ├── base.py          # 工具基类 + 注册机制
│   └── enterprise_tools.py  # 5 个企业开发工具
├── knowledge/
│   ├── ingest.py        # 文档向量化入库
│   └── docs/            # 知识库源文档
└── utils/
    ├── logger.py
    └── exception.py
```

## ⚙️ 配置项

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `LLM_API_KEY` | API 密钥 | — |
| `LLM_BASE_URL` | API 地址（兼容 OpenAI 格式） | `https://api.openai.com/v1` |
| `LLM_MODEL_NAME` | 模型名称 | `gpt-4` |
| `LLM_TEMPERATURE` | 温度参数 | 0.7 |
| `LLM_MAX_TOKENS` | 最大 token | 2048 |
| `VECTORSTORE_EMBEDDING_MODEL` | 嵌入模型 | `text-embedding-ada-002` |
| `MEMORY_MAX_HISTORY` | 最大历史条数 | 100 |

## 📜 License

MIT
