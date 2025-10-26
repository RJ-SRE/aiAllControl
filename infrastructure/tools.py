"""
工具定义模块 - Tools Definition

定义可供AI调用的工具(Function Calling),实现AI的动作执行能力。

设计模式:
1. 声明式工具定义 - 使用JSON Schema定义工具签名
2. 可扩展架构 - 轻松添加新工具

支持的工具类别:
1. 软件包管理 - 搜索、安装软件
2. Mac应用控制 - 打开、关闭、查询应用状态
3. 系统查询 - 获取系统信息

使用示例:
    from infrastructure.tools import TOOLS, get_tool_schemas
    
    schemas = get_tool_schemas()
    response = ai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=schemas
    )
"""

from typing import List, Dict, Any


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_software",
            "description": "搜索macOS软件包,支持自然语言描述。例如: '绘图软件'、'视频编辑器'等",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或自然语言描述,例如: '绘图软件'、'可以画流程图的工具'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回的结果数量,默认5个",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_software",
            "description": "安装macOS软件包。注意: 这是敏感操作,执行前需要向用户确认",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {
                        "type": "string",
                        "description": "要安装的软件包名称,例如: 'drawio'、'visual-studio-code'"
                    }
                },
                "required": ["package_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_installed_software",
            "description": "列出当前系统已安装的所有软件包",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "打开Mac应用程序",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "应用程序名称,例如: 'Safari'、'Chrome'、'Visual Studio Code'"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "quit_app",
            "description": "关闭Mac应用程序",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "应用程序名称,例如: 'Safari'、'Chrome'"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_app_status",
            "description": "检查Mac应用程序是否正在运行",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "应用程序名称,例如: 'Safari'、'Chrome'"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "获取macOS系统信息,包括版本号等",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    获取工具定义列表
    
    返回:
        List[Dict]: 工具定义的JSON Schema列表
    
    说明:
        返回符合OpenAI Function Calling格式的工具定义
    
    示例:
        >>> schemas = get_tool_schemas()
        >>> len(schemas)
        7
    """
    return TOOLS


def get_tool_names() -> List[str]:
    """
    获取所有工具的名称列表
    
    返回:
        List[str]: 工具名称列表
    
    示例:
        >>> names = get_tool_names()
        >>> 'search_software' in names
        True
    """
    return [tool["function"]["name"] for tool in TOOLS]


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """
    根据名称获取工具定义
    
    参数:
        name: 工具名称
    
    返回:
        Dict: 工具定义,如果不存在返回None
    
    示例:
        >>> tool = get_tool_by_name("search_software")
        >>> tool["function"]["name"]
        'search_software'
    """
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None
