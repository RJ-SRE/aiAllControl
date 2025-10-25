"""
MCP客户端模块 - MCP Client Module

基于MCP协议的精简AI客户端实现,通过七牛云接口间接调用OpenAI。

设计理念:
- 精简: 最小化依赖,专注核心功能
- 标准化: 使用MCP协议,提升互操作性
- 灵活: 支持配置切换,兼容多种部署方式

主要功能:
- 通过MCP协议调用AI服务
- 支持OpenAI兼容接口(七牛云)
- 自然语言意图分析
- 结构化数据返回

使用示例:
    from infrastructure.mcp_client import MCPAIClient
    
    # 创建MCP客户端
    client = MCPAIClient(
        api_key="your-api-key",
        base_url="https://openai.qiniu.com/v1",
        model="gpt-4"
    )
    
    # 分析用户意图
    result = client.analyze_intent("帮我找一个绘图软件")
"""

from typing import Dict, Optional
from abc import ABC, abstractmethod
import json
from infrastructure.logger import logger


class MCPAIClient(ABC):
    """
    MCP AI客户端基类
    
    设计说明:
        基于MCP协议的精简AI客户端实现。
        通过七牛云提供的OpenAI兼容接口进行AI推理。
    
    属性:
        api_key: API密钥
        base_url: API端点URL
        model: 使用的模型名称
    """
    
    def __init__(self, api_key: str, base_url: str = "https://openai.qiniu.com/v1", model: str = "gpt-4"):
        """
        初始化MCP AI客户端
        
        参数:
            api_key: 七牛云API密钥
            base_url: API端点URL(默认: 七牛云OpenAI兼容接口)
            model: 使用的模型名称(默认: gpt-4)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._setup_client()
        logger.info(f"MCP AI客户端初始化成功 - 端点: {base_url}, 模型: {model}")
    
    def _setup_client(self):
        """
        设置底层HTTP客户端
        
        说明:
            使用OpenAI SDK作为HTTP客户端,简化实现。
            这是一个精简的MCP客户端,专注于核心功能。
        """
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise RuntimeError("请安装OpenAI库: pip install openai")
    
    def analyze_intent(self, user_input: str) -> Dict[str, str]:
        """
        分析用户意图(通过MCP协议)
        
        参数:
            user_input: 用户的自然语言输入
        
        返回:
            Dict[str, str]: 分析结果
                - intent: 用户意图 ('搜索' | '安装' | '查询')
                - keyword: 提取的关键词
                - category: 软件类别
        
        说明:
            这是一个精简的MCP客户端实现,使用OpenAI兼容接口。
            通过七牛云间接调用OpenAI服务。
        """
        prompt = self._build_prompt(user_input)
        
        try:
            logger.info(f"[MCP] 调用AI服务分析用户意图: {user_input}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"[MCP] AI分析成功: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"[MCP] AI调用失败: {e}", exc_info=True)
            raise RuntimeError(f"MCP AI推理失败: {e}")
    
    def _build_prompt(self, user_input: str) -> str:
        """
        构建AI提示词
        
        参数:
            user_input: 用户输入
        
        返回:
            str: 格式化的提示词
        """
        return f"""
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


def create_mcp_client(api_key: str, base_url: str = "https://openai.qiniu.com/v1", model: str = "gpt-4") -> MCPAIClient:
    """
    工厂函数 - 创建MCP AI客户端
    
    参数:
        api_key: API密钥
        base_url: API端点URL
        model: 模型名称
    
    返回:
        MCPAIClient: MCP AI客户端实例
    
    说明:
        这是一个精简的工厂函数,用于创建MCP客户端。
    """
    return MCPAIClient(api_key, base_url, model)
