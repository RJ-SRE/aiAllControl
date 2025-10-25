"""
日志模块 - Logger Module

提供统一的日志接口，支持控制台和文件双输出。

设计模式: 单例模式 (Singleton Pattern)
- 确保全局只有一个日志实例
- 避免重复初始化和配置

主要功能:
1. 控制台输出 - INFO级别及以上
2. 文件记录 - DEBUG级别及以上，按日期滚动
3. 格式化输出 - 包含时间戳、级别、模块、行号
4. 自动创建日志目录

使用示例:
    from infrastructure.logger import logger
    
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息", exc_info=True)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """
    日志管理器 - 单例模式实现
    
    属性:
        _instance: 类级别的单例实例
        _initialized: 标记是否已初始化
        logger: Python标准logging对象
    
    设计说明:
        使用__new__方法实现单例，确保无论创建多少次Logger对象，
        都返回同一个实例，避免重复配置日志系统。
    """
    
    # 类变量：存储唯一实例
    _instance: Optional['Logger'] = None
    
    def __new__(cls):
        """
        控制对象创建，实现单例模式
        
        返回:
            Logger: 全局唯一的Logger实例
        
        工作原理:
            第一次调用时创建新实例，后续调用返回已有实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化日志配置
        
        说明:
            使用_initialized标志避免重复初始化，
            因为单例模式下__init__会被多次调用
        """
        # 检查是否已初始化，避免重复配置
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._setup_logger()
    
    def _setup_logger(self):
        """
        配置日志系统的核心方法
        
        配置内容:
        1. 创建日志目录: ~/.macmind/logs/
        2. 生成日志文件: macmind_YYYYMMDD.log
        3. 配置日志格式: [时间] 级别 模块:行号 - 消息
        4. 设置双输出: 控制台(INFO+) 和 文件(DEBUG+)
        
        日志级别说明:
        - DEBUG: 详细的调试信息，仅记录到文件
        - INFO: 一般信息，控制台和文件都记录
        - WARNING: 警告信息
        - ERROR: 错误信息
        """
        # 步骤1: 创建日志目录
        # 日志存放在用户主目录的 .macmind/logs/ 下
        log_dir = Path.home() / '.macmind' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 步骤2: 生成日志文件名，按日期区分
        # 格式: macmind_20241025.log
        log_file = log_dir / f"macmind_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 步骤3: 获取Python标准logger实例
        self.logger = logging.getLogger('MacMind')
        self.logger.setLevel(logging.DEBUG)  # 设置最低级别为DEBUG
        
        # 步骤4: 定义日志格式
        # 格式说明:
        # [2024-10-25 10:30:45] INFO     MacMind:42 - 这是一条日志
        # [时间戳] 级别(8字符宽) 模块名:行号 - 消息内容
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 步骤5: 配置控制台输出处理器
        # 用途: 实时查看程序运行状态
        # 级别: INFO及以上（过滤DEBUG信息，避免控制台过于冗余）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 步骤6: 配置文件输出处理器
        # 用途: 完整记录所有日志，用于问题排查
        # 级别: DEBUG及以上（记录所有信息）
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 步骤7: 将处理器添加到logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """
        记录调试信息
        
        参数:
            message: 调试消息内容
        
        使用场景:
            - 变量值的跟踪
            - 函数调用流程
            - 详细的执行步骤
        
        示例:
            logger.debug(f"搜索关键词: {keyword}")
            logger.debug(f"找到{len(results)}个结果")
        """
        self.logger.debug(message)
    
    def info(self, message: str):
        """
        记录一般信息
        
        参数:
            message: 信息内容
        
        使用场景:
            - 程序正常运行状态
            - 重要操作的开始/完成
            - 业务流程的关键节点
        
        示例:
            logger.info("开始搜索软件包")
            logger.info(f"成功安装: {package_name}")
        """
        self.logger.info(message)
    
    def warning(self, message: str):
        """
        记录警告信息
        
        参数:
            message: 警告消息
        
        使用场景:
            - 潜在的问题
            - 不推荐的操作
            - 配置不完整但可以继续运行
        
        示例:
            logger.warning("API配置未找到，使用默认值")
            logger.warning("缓存已过期，将重新获取")
        """
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """
        记录错误信息
        
        参数:
            message: 错误消息
            exc_info: 是否包含异常堆栈信息（默认False）
        
        使用场景:
            - 操作失败
            - 异常捕获
            - 严重错误
        
        示例:
            logger.error("安装失败")
            logger.error("API调用失败", exc_info=True)  # 包含完整堆栈
        """
        self.logger.error(message, exc_info=exc_info)


# 模块级全局实例
# 其他模块可以直接导入使用: from infrastructure.logger import logger
logger = Logger()
