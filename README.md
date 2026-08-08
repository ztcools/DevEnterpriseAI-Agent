# DevEnterpriseAI Agent

Private on-prem AI dev assistant for enterprise intranets — ReAct agent + custom tool routing + RAG knowledge base + conversation memory.

## What it solves

Teams need a unified AI coding assistant that embeds their own coding standards, historical pitfalls, and build flows — public Copilot won't cut it. This tool supports on-prem deployment and is OpenAI-API compatible, working with any local or remote LLM.

## Tech stack

Python 3 · LangChain · Chroma vector store · pydantic-settings · OpenAI-compatible API

## Features

- **ReAct orchestration**: the LLM judges intent — direct chat for non-tool cases, picks and runs tools when needed
- **5 enterprise tools**: code generation (with built-in coding standards) · refactoring · compile-error analysis · API/class doc generation · automation script generation
- **Custom tool routing**: a hand-maintained tool mapping dict, no LLM function-calling dependency — more controllable
- **RAG knowledge base**: company docs stored in Chroma for retrieval-augmented generation
- **Conversation memory**: automatic summarization of history to prevent context overflow

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env   # edit to fill in API key / base_url / model
python main.py
```
