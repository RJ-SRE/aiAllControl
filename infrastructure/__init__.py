"""
Infrastructure Layer - 基础设施层

该层提供应用程序的基础技术支持，包括:
- 日志管理 (logger.py)
- 配置管理 (config.py)
- Homebrew命令执行 (brew_executor.py)
- AI客户端封装 (ai_client.py)

设计原则:
1. 单一职责 - 每个模块只负责一个技术关注点
2. 低耦合 - 模块之间相互独立，可单独替换
3. 高内聚 - 相关功能集中在同一模块中
"""

__version__ = "0.1.0"
