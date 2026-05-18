# -*- coding: utf-8 -*-
"""
DevEnterpriseAI - 企业私有化AI开发Agent

一键启动入口文件
"""

import sys
import os
import traceback

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_environment():
    """设置运行环境"""
    from utils.logger import setup_logger
    
    # 初始化日志
    setup_logger()
    
    # 检查必要目录
    directories = [
        "knowledge/docs",
        "knowledge/vectorstore",
        "logs",
        ".chroma"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"📁 创建目录: {full_path}")


def init_knowledge_base():
    """初始化知识库（首次运行时执行）"""
    from knowledge import KnowledgeIngestor, create_ingestor
    
    try:
        ingestor = create_ingestor()
        docs_dir = os.path.join(os.path.dirname(__file__), "knowledge/docs")
        
        # 检查是否已有向量库
        vectorstore_path = os.path.join(os.path.dirname(__file__), "knowledge/vectorstore")
        if not os.listdir(vectorstore_path):
            print("📚 首次启动，正在构建知识库...")
            ingestor.ingest_directory(docs_dir, file_types=[".txt", ".md"])
            ingestor.persist()
            print("✅ 知识库构建完成")
        else:
            print("📚 加载已有知识库")
    except Exception as e:
        print(f"⚠️ 知识库初始化失败: {e}")


def main():
    """主入口函数"""
    print("🚀 DevEnterpriseAI 启动中...")
    print("=" * 60)
    
    try:
        # 1. 设置环境
        setup_environment()
        
        # 2. 初始化知识库
        init_knowledge_base()
        
        # 3. 创建Agent
        from core import create_agent
        
        print("🤖 创建Agent实例...")
        agent = create_agent(verbose=True)
        print("✅ Agent创建完成")
        
        print("\n" + "=" * 60)
        print("🎯 DevEnterpriseAI 企业级AI助手已就绪")
        print("💡 支持：代码生成、代码重构、编译错误分析、文档生成、自动化脚本")
        print("📖 输入 'help' 查看帮助，输入 'exit' 退出")
        print("=" * 60)
        
        # 4. 主交互循环
        while True:
            try:
                user_input = input("\n🤔 请输入你的问题: ").strip()
                
                if not user_input:
                    continue
                
                # 命令处理
                if user_input.lower() == "exit":
                    print("👋 感谢使用 DevEnterpriseAI，再见！")
                    break
                
                if user_input.lower() == "help":
                    print("\n📋 可用命令:")
                    print("  exit    - 退出系统")
                    print("  help    - 显示帮助信息")
                    print("  clear   - 清空屏幕")
                    print("  reset   - 重置对话历史")
                    continue
                
                if user_input.lower() == "clear":
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                
                if user_input.lower() == "reset":
                    agent._memory.clear()
                    print("🔄 对话历史已重置")
                    continue
                
                # 5. 执行Agent
                print("\n" + "-" * 60)
                print(f"📝 用户输入: {user_input}")
                print("-" * 60)
                
                response = agent.chat(user_input)
                
                # 6. 输出结果
                print("\n" + "=" * 60)
                print("💡 Agent回答:")
                print("-" * 60)
                print(response)
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，再见！")
                break
            except Exception as e:
                print(f"\n❌ 执行异常: {e}")
                traceback.print_exc()
                print("⚠️ 请重试或输入其他问题")
    
    except Exception as e:
        print(f"\n💀 启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()