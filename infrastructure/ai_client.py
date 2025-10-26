"""
AI客户端模块 - AI Client Module

封装AI API调用,使用七牛云大模型推理服务。

设计模式:
1. 策略模式 (Strategy Pattern) - 使用统一的AIClient接口
2. 工厂模式 (Factory Pattern) - 通过工厂函数创建客户端

支持的AI提供商:
- 七牛云大模型推理服务 (使用 OpenAI 兼容接口)

主要功能:
- 分析用户的自然语言输入
- 提取关键词和意图
- 返回结构化数据

错误处理:
- AI调用失败时立即抛出异常,停止执行
- 详细的错误日志记录
- 不再使用降级机制

使用示例:
    from infrastructure.ai_client import create_ai_client
    
    # 创建AI客户端
    client = create_ai_client()
    
    # 分析用户意图
    result = client.analyze_intent("帮我找一个绘图软件")
    # 返回: {
    #     'intent': '搜索',
    #     'keyword': '绘图软件',
    #     'category': '绘图'
    # }
"""

from typing import Dict
from abc import ABC, abstractmethod
from infrastructure.config import config
from infrastructure.logger import logger
from domain.exceptions import AIError, ConfigError


class AIClient(ABC):
    """
    AI客户端抽象基类
    
    设计说明:
        定义AI客户端的标准接口,所有具体实现必须
        继承此类并实现analyze_intent方法。
    
    设计模式: 策略模式
        不同的AI提供商作为不同的策略,可以互换使用。
    """
    
    @abstractmethod
    def analyze_intent(self, user_input: str) -> Dict[str, str]:
        """
        分析用户意图的抽象方法
        
        参数:
            user_input: 用户的自然语言输入
        
        返回:
            Dict[str, str]: 包含以下键的字典
                - intent: 用户意图 ('搜索' | '安装' | '查询')
                - keyword: 提取的关键词
                - category: 软件类别(如: 绘图/视频/编程等)
        
        说明:
            所有继承类必须实现此方法
        """
        pass


class QiniuClient(AIClient):
    """
    七牛云大模型推理客户端
    
    属性:
        client: OpenAI SDK客户端实例(七牛云兼容OpenAI接口)
        model: 使用的模型名称
    
    说明:
        使用七牛云的大模型推理服务进行自然语言理解。
        七牛云提供 OpenAI 兼容的 API 端点。
    """
    
    def __init__(self, api_key: str, base_url: str = "https://openai.qiniu.com/v1", model: str = "gpt-4"):
        """
        初始化七牛云AI客户端
        
        参数:
            api_key: 七牛云 API 密钥
            base_url: 七牛云 API 端点 URL(默认: https://openai.qiniu.com/v1)
            model: 使用的模型名称(默认: gpt-4)
        
        抛出:
            RuntimeError: 如果openai库未安装
        
        说明:
            需要先安装: pip install openai
            七牛云提供 OpenAI 兼容接口,可直接使用 OpenAI SDK
        """
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            self.model = model
            logger.debug(f"七牛云AI客户端初始化成功 - 端点: {base_url}, 模型: {model}")
        except ImportError:
            raise ConfigError(
                "OpenAI库未安装",
                detail="请运行: pip install openai"
            )
    
    def analyze_intent(self, user_input: str) -> Dict[str, str]:
        """
        使用七牛云大模型分析用户意图
        
        参数:
            user_input: 用户的自然语言输入
        
        返回:
            Dict[str, str]: 分析结果
                - intent: 用户意图
                - keyword: 关键词
                - category: 软件类别
        
        抛出:
            Exception: API调用失败时抛出异常,不再使用降级策略
        
        工作流程:
        1. 构建提示词(Prompt Engineering)
        2. 调用七牛云大模型 API
        3. 解析JSON响应
        4. 失败时抛出异常(不再降级)
        
        提示词设计:
            采用结构化输出,要求AI返回JSON格式,
            便于程序解析和处理。
        
        示例:
            输入: "帮我找一个可以画流程图的工具"
            输出: {
                'intent': '搜索',
                'keyword': '流程图',
                'category': '绘图'
            }
        """
        prompt = f"""
分析以下用户请求,提取关键信息:

用户输入: "{user_input}"

请以JSON格式返回:
{{
    "intent": "搜索|安装|查询",
    "keyword": "软件关键词",
    "category": "软件类别(如: 绘图/视频/编程等)"
}}

只返回JSON,不要其他文字。
"""
        
        try:
            logger.debug(f"调用七牛云大模型分析用户意图: {user_input}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.debug(f"七牛云AI分析成功: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"七牛云AI调用失败: {e}", exc_info=True)
            raise AIError(
                "AI模型推理失败",
                detail=str(e),
                context={'model': self.model, 'input': user_input[:50]}
            )


def create_ai_client() -> AIClient:
    """
    工厂函数 - 创建AI客户端
    
    返回:
        AIClient: 七牛云AI客户端实例
    
    抛出:
        ConfigError: API密钥未配置
    
    设计模式: 工厂模式
        简化的工厂函数,统一使用七牛云AI客户端。
    
    配置说明:
        - qiniu_api_key: 七牛云 API 密钥(从环境变量或配置文件读取)
        - qiniu_base_url: 七牛云 API 端点 URL(可选,默认: https://openai.qiniu.com/v1)
        - qiniu_model: 使用的模型名称(可选,默认: gpt-4)
    
    示例:
        # 创建AI客户端
        client = create_ai_client()
        result = client.analyze_intent("帮我找一个绘图软件")
    """
    api_key = config.get('qiniu_api_key')
    if not api_key:
        raise ConfigError(
            "未配置七牛云 API Key",
            detail="请在配置文件 ~/.macmind/config.json 中设置 qiniu_api_key,或设置环境变量 QINIU_API_KEY",
            context={'config_url': 'https://developer.qiniu.com/aitokenapi/12884/how-to-get-api-key'}
        )
    
    base_url = config.get('qiniu_base_url', 'https://openai.qiniu.com/v1')
    model = config.get('qiniu_model', 'gpt-4')
    
    logger.info(f"创建七牛云AI客户端 - 模型: {model}")
    return QiniuClient(api_key, base_url, model)
