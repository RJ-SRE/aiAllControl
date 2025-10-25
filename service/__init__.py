"""
业务逻辑层 - Service Layer

设计思想：Service模式
- 协调多个Repository和Domain对象完成业务流程
- 封装复杂的业务逻辑，提供简洁的API
- 处理事务边界和业务规则

职责：
1. 调用AI分析用户意图
2. 搜索并排序软件包
3. 安装/卸载软件
4. 列出已安装软件
5. 协调Repository和Domain层的交互

业务流程示例：
    用户输入 "帮我安装一个绘图软件"
        ↓
    AI分析意图（提取关键词：绘图）
        ↓
    搜索软件包
        ↓
    智能排序（开源优先、下载量、活跃度）
        ↓
    展示推荐列表
        ↓
    用户确认后安装

架构位置：
    Controller Layer (控制器层) - 待实现
        ↓
    Service Layer (业务逻辑层) ← 本层
        ↓
    Repository Layer (数据访问层) - 已实现
        ↓
    Domain Layer (领域模型层) - 已实现
        ↓
    Infrastructure Layer (基础设施层) - 已实现

核心类：
- PackageService: 软件包管理服务
"""

from service.package_service import PackageService

__all__ = ['PackageService']
