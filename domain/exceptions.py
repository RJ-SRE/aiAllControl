"""
自定义异常体系 - Custom Exceptions

统一的异常定义,提供清晰的错误分类和详细的错误信息。

设计模式: 异常层次结构
- 基础异常类: MacMindError
- 分类异常: 按模块和功能分类
- 详细错误信息: 包含上下文和调试信息

异常分类:
1. ConfigError - 配置相关错误
2. BrewError - Homebrew操作错误
3. AIError - AI服务错误
4. PackageError - 软件包操作错误
5. ValidationError - 数据验证错误

使用示例:
    from domain.exceptions import BrewError, ConfigError
    
    if not api_key:
        raise ConfigError("未配置API密钥", detail="请设置环境变量 QINIU_API_KEY")
    
    try:
        brew.install(package_name)
    except BrewError as e:
        logger.error(f"安装失败: {e}")
"""

from typing import Optional, Dict, Any


class MacMindError(Exception):
    """
    MacMind基础异常类
    
    所有自定义异常的基类,提供统一的错误处理接口。
    
    属性:
        message: 错误消息
        detail: 详细错误信息(可选)
        context: 错误上下文信息(可选)
    
    设计说明:
        使用基础异常类便于统一捕获所有MacMind相关错误
    """
    
    def __init__(
        self, 
        message: str, 
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        参数:
            message: 错误消息
            detail: 详细错误信息
            context: 错误上下文(如: {'package': 'vim', 'operation': 'install'})
        """
        self.message = message
        self.detail = detail
        self.context = context or {}
        
        full_message = message
        if detail:
            full_message = f"{message}: {detail}"
        
        super().__init__(full_message)
    
    def __str__(self) -> str:
        """
        字符串表示
        
        返回:
            包含消息和上下文的完整错误信息
        """
        parts = [self.message]
        
        if self.detail:
            parts.append(f"详情: {self.detail}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"上下文: {context_str}")
        
        return " | ".join(parts)


class ConfigError(MacMindError):
    """
    配置错误
    
    使用场景:
    - API密钥未配置
    - 配置文件格式错误
    - 配置值不合法
    - Homebrew路径不存在
    
    示例:
        raise ConfigError(
            "API密钥未配置",
            detail="请设置环境变量 QINIU_API_KEY 或在配置文件中添加",
            context={'config_file': '~/.macmind/config.json'}
        )
    """
    pass


class BrewError(MacMindError):
    """
    Homebrew操作错误
    
    使用场景:
    - brew命令执行失败
    - 软件包不存在
    - 安装/卸载失败
    - 命令超时
    
    示例:
        raise BrewError(
            "软件包安装失败",
            detail="命令返回非零退出码",
            context={'package': 'drawio', 'exit_code': 1}
        )
    """
    pass


class AIError(MacMindError):
    """
    AI服务错误
    
    使用场景:
    - API调用失败
    - 网络连接超时
    - API密钥无效
    - 响应格式错误
    - 配额超限
    
    示例:
        raise AIError(
            "AI服务调用失败",
            detail="网络连接超时",
            context={'api': 'qiniu', 'timeout': 30}
        )
    """
    pass


class PackageError(MacMindError):
    """
    软件包操作错误
    
    使用场景:
    - 软件包信息获取失败
    - 软件包数据格式错误
    - 依赖关系解析失败
    
    示例:
        raise PackageError(
            "软件包信息不完整",
            detail="缺少必需字段: version",
            context={'package': 'vim'}
        )
    """
    pass


class ValidationError(MacMindError):
    """
    数据验证错误
    
    使用场景:
    - 包名为空
    - 版本号格式错误
    - 许可证类型不合法
    - 依赖关系循环
    
    示例:
        raise ValidationError(
            "包名不能为空",
            detail="Package对象创建失败",
            context={'field': 'name'}
        )
    """
    pass


class MacControlError(MacMindError):
    """
    Mac系统控制错误
    
    使用场景:
    - AppleScript执行失败
    - 应用未找到
    - 权限不足
    - 系统命令超时
    
    示例:
        raise MacControlError(
            "应用关闭失败",
            detail="应用未运行",
            context={'app': '网易云音乐'}
        )
    """
    pass


class ConversationError(MacMindError):
    """
    会话管理错误
    
    使用场景:
    - 会话历史损坏
    - 上下文超出限制
    - 会话持久化失败
    
    示例:
        raise ConversationError(
            "会话历史超出限制",
            detail="最多保留100条消息",
            context={'current': 150, 'max': 100}
        )
    """
    pass
