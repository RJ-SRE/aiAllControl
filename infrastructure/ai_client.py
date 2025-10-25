"""
AI客户端模块 - AI Client Module

封装AI API调用，支持多种AI提供商。

设计模式:
1. 策略模式 (Strategy Pattern) - 支持多种AI提供商
2. 工厂模式 (Factory Pattern) - 通过工厂函数创建客户端

支持的AI提供商:
- Anthropic Claude (默认)
- OpenAI GPT (可扩展)

主要功能:
- 分析用户的自然语言输入
- 提取关键词和意图
- 返回结构化数据

错误处理:
- AI调用失败时降级到直接使用用户输入
- 详细的错误日志记录
- 容错机制确保程序继续运行

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


class AIClient(ABC):
    """
    AI客户端抽象基类
    
    设计说明:
        定义AI客户端的标准接口，所有具体实现必须
        继承此类并实现analyze_intent方法。
    
    设计模式: 策略模式
        不同的AI提供商作为不同的策略，可以互换使用。
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
                - category: 软件类别（如: 绘图/视频/编程等）
        
        说明:
            所有继承类必须实现此方法
        """
        pass


class AnthropicClient(AIClient):
    """
    Anthropic Claude AI客户端
    
    属性:
        client: Anthropic SDK客户端实例
    
    说明:
        使用Anthropic的Claude模型进行自然语言理解。
        模型: claude-3-5-sonnet-20241022
    """
    
    def __init__(self, api_key: str):
        """
        初始化Anthropic客户端
        
        参数:
            api_key: Anthropic API密钥
        
        抛出:
            RuntimeError: 如果anthropic库未安装
        
        说明:
            需要先安装: pip install anthropic
        """
        try:
            # 动态导入anthropic库
            # 这样设计的好处：不使用Anthropic时无需安装该库
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise RuntimeError("请安装Anthropic库: pip install anthropic")
    
    def analyze_intent(self, user_input: str) -> Dict[str, str]:
        """
        使用Claude分析用户意图
        
        参数:
            user_input: 用户的自然语言输入
        
        返回:
            Dict[str, str]: 分析结果
                - intent: 用户意图
                - keyword: 关键词
                - category: 软件类别
        
        工作流程:
        1. 构建提示词（Prompt Engineering）
        2. 调用Claude API
        3. 解析JSON响应
        4. 错误处理和降级
        
        提示词设计:
            采用结构化输出，要求AI返回JSON格式，
            便于程序解析和处理。
        
        示例:
            输入: "帮我找一个可以画流程图的工具"
            输出: {
                'intent': '搜索',
                'keyword': '流程图',
                'category': '绘图'
            }
        """
        # 步骤1: 构建提示词
        # 提示词工程的关键点：
        # 1. 明确任务：分析用户请求
        # 2. 指定格式：JSON
        # 3. 提供示例：通过描述让AI理解输出格式
        # 4. 约束输出：只返回JSON，不要其他文字
        prompt = f"""
分析以下用户请求，提取关键信息:

用户输入: "{user_input}"

请以JSON格式返回:
{{
    "intent": "搜索|安装|查询",
    "keyword": "软件关键词",
    "category": "软件类别(如: 绘图/视频/编程等)"
}}

只返回JSON，不要其他文字。
"""
        
        try:
            # 步骤2: 调用Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # 使用最新的Claude 3.5模型
                max_tokens=1024,  # 限制输出长度
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 步骤3: 解析响应
            # Claude的响应格式: message.content[0].text
            import json
            result = json.loads(message.content[0].text)
            
            # 记录分析结果（调试用）
            logger.debug(f"AI分析结果: {result}")
            
            return result
            
        except Exception as e:
            # 步骤4: 错误处理和降级
            # 如果AI调用失败（网络错误、API错误、解析错误等），
            # 降级策略：直接使用用户输入作为关键词
            logger.error(f"AI分析失败: {e}", exc_info=True)
            
            # 返回降级结果
            # 虽然缺少AI分析，但不影响核心功能
            return {
                'intent': '搜索',  # 默认意图为搜索
                'keyword': user_input,  # 直接使用用户输入
                'category': ''  # 类别留空
            }


class OpenAIClient(AIClient):
    """
    OpenAI GPT客户端
    
    属性:
        client: OpenAI SDK客户端实例
    
    说明:
        使用OpenAI的GPT模型进行自然语言理解。
        这是一个示例实现，展示如何支持多个AI提供商。
    """
    
    def __init__(self, api_key: str):
        """
        初始化OpenAI客户端
        
        参数:
            api_key: OpenAI API密钥
        
        抛出:
            RuntimeError: 如果openai库未安装
        """
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise RuntimeError("请安装OpenAI库: pip install openai")
    
    def analyze_intent(self, user_input: str) -> Dict[str, str]:
        """
        使用GPT分析用户意图
        
        参数:
            user_input: 用户输入
        
        返回:
            Dict[str, str]: 分析结果
        
        说明:
            实现与AnthropicClient类似，但使用OpenAI的API。
        """
        prompt = f"""
分析用户请求，提取关键信息:

用户输入: "{user_input}"

返回JSON格式:
{{
    "intent": "搜索|安装|查询",
    "keyword": "软件关键词",
    "category": "软件类别"
}}
"""
        
        try:
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}  # 强制JSON输出
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            # 降级处理
            logger.error(f"AI分析失败: {e}", exc_info=True)
            return {
                'intent': '搜索',
                'keyword': user_input,
                'category': ''
            }


def create_ai_client() -> AIClient:
    """
    工厂函数 - 根据配置创建AI客户端
    
    返回:
        AIClient: AI客户端实例
    
    抛出:
        RuntimeError: API密钥未配置
        ValueError: 不支持的AI提供商
    
    设计模式: 工厂模式
        根据配置动态创建不同的AI客户端，
        调用者无需关心具体实现。
    
    配置说明:
        - api_key: 从环境变量读取
        - api_provider: 'anthropic' 或 'openai'
    
    扩展方式:
        如需支持新的AI提供商：
        1. 创建新的Client类，继承AIClient
        2. 实现analyze_intent方法
        3. 在此函数添加对应的分支
    
    示例:
        # 自动根据配置创建客户端
        client = create_ai_client()
        result = client.analyze_intent("搜索绘图软件")
    """
    # 步骤1: 读取API密钥
    api_key = config.get('api_key')
    if not api_key:
        raise RuntimeError("未配置API Key，请设置环境变量 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")
    
    # 步骤2: 读取AI提供商配置
    provider = config.get('api_provider', 'anthropic')
    
    # 步骤3: 根据配置创建对应的客户端
    if provider == 'anthropic':
        return AnthropicClient(api_key)
    elif provider == 'openai':
        return OpenAIClient(api_key)
    else:
        raise ValueError(f"不支持的AI提供商: {provider}")
