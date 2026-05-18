# -*- coding: utf-8 -*-
"""
DevEnterpriseAI Agent 演示脚本

展示Agent核心调度层的使用方式。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import create_agent


def main():
    """Agent演示主函数"""
    print("🚀 DevEnterpriseAI Agent 演示")
    print("="*60)
    print("这是一个企业级AI开发助手，支持代码生成、重构、编译错误分析等功能。")
    print("输入 'exit' 或 'quit' 退出。")
    print("="*60)
    
    # 创建Agent实例
    agent = create_agent(verbose=True)
    
    while True:
        try:
            user_input = input("\n🤔 请输入你的问题: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 再见！")
                break
            
            if not user_input.strip():
                print("⚠️ 请输入有效的问题")
                continue
            
            # 运行Agent
            response = agent.chat(user_input)
            
            print("\n💡 Agent回答:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")


if __name__ == "__main__":
    main()