"""
Repository Layer (仓储层) - 数据访问层

设计思想：Repository模式
- 封装数据访问逻辑，为Service层提供统一的数据接口
- 隐藏底层数据源的实现细节（Homebrew API、本地缓存等）
- 支持多种数据源的切换和扩展

职责：
1. 数据访问：调用Infrastructure层的brew_executor
2. 数据转换：Homebrew格式 → Domain实体
3. 缓存管理：提升性能，减少API调用
4. 查询接口：提供各种查询方法

核心模块：
- PackageRepository: 软件包仓储，提供搜索、查询、缓存等功能

设计原则：
- 单一数据源抽象：上层不关心数据来自API还是缓存
- 透明缓存：自动管理缓存的读写和失效
- 数据转换集中：统一将外部数据转换为Domain实体
"""
