"""
自定义异常体系 - Custom Exception Hierarchy

提供统一的异常处理机制,增强错误信息的可读性和可调试性。

设计模式: 异常层次结构
- 基础异常类MacMindError作为所有自定义异常的父类
- 按功能模块划分不同的异常类型
- 支持携带上下文信息(如操作对象、原始异常)

异常分类:
1. ConfigError - 配置相关错误
2. BrewError - Homebrew操作错误
3. AIError - AI服务错误
4. PackageError - 软件包操作错误
5. ValidationError - 数据验证错误
6. MacControlError - Mac系统控制错误
7. ConversationError - 会话管理错误

使用示例:
    from domain.exceptions import BrewError, ConfigError
    
    # 抛出配置错误
    if not api_key:
        raise ConfigError("缺少API密钥", config_key="qiniu_api_key")
    
    # 抛出Homebrew错误
    try:
        brew.install("package")
    except Exception as e:
        raise BrewError("安装失败", package="package", cause=e)
"""

from typing import Optional, Any, Dict


class MacMindError(Exception):
    """
    MacMind基础异常类
    
    所有自定义异常的父类,提供统一的异常处理接口。
    
    属性:
        message: 错误消息
        context: 错误上下文信息(字典)
        cause: 原始异常(如果有)
    
    设计思想:
        - 提供丰富的错误上下文
        - 支持异常链(cause参数)
        - 便于日志记录和调试
    """
    
    def __init__(self, message: str, cause: Optional[Exception] = None, **context):
        """
        初始化基础异常
        
        参数:
            message: 错误消息
            cause: 原始异常(可选)
            **context: 错误上下文信息(键值对)
        
        示例:
            raise MacMindError(
                "操作失败",
                cause=original_error,
                operation="install",
                package="vim"
            )
        """
        self.message = message
        self.context = context
        self.cause = cause
        
        error_parts = [message]
        
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            error_parts.append(f"({context_str})")
        
        if cause:
            error_parts.append(f"原因: {str(cause)}")
        
        super().__init__(" | ".join(error_parts))
    
    def __repr__(self) -> str:
        """返回异常的详细字符串表示"""
        return f"{self.__class__.__name__}({self.message}, context={self.context})"


class ConfigError(MacMindError):
    """
    配置错误
    
    配置文件缺失、格式错误、参数无效等情况。
    
    使用场景:
        - 配置文件不存在或无法读取
        - 配置参数缺失或无效
        - 配置验证失败
    
    示例:
        raise ConfigError(
            "配置文件格式错误",
            config_file="~/.macmind/config.json",
            cause=json_decode_error
        )
    """
    pass


class BrewError(MacMindError):
    """
    Homebrew操作错误
    
    Homebrew命令执行失败、超时、软件包不存在等情况。
    
    使用场景:
        - brew命令执行失败
        - 软件包搜索无结果
        - 安装/卸载操作失败
        - Homebrew不可用或路径错误
    
    示例:
        raise BrewError(
            "软件包安装失败",
            package="drawio",
            command="brew install drawio",
            cause=subprocess_error
        )
    """
    pass


class AIError(MacMindError):
    """
    AI服务错误
    
    AI API调用失败、响应解析错误、配额超限等情况。
    
    使用场景:
        - API密钥无效或过期
        - API请求超时或失败
        - API响应格式错误
        - API配额超限
    
    示例:
        raise AIError(
            "AI服务调用失败",
            provider="qiniu",
            model="gpt-4",
            cause=api_exception
        )
    """
    pass


class PackageError(MacMindError):
    """
    软件包操作错误
    
    软件包查询、安装、卸载等业务逻辑错误。
    
    使用场景:
        - 软件包不存在
        - 软件包信息不完整
        - 依赖冲突
        - 安装状态异常
    
    示例:
        raise PackageError(
            "软件包不存在",
            package="nonexistent-package",
            operation="install"
        )
    """
    pass


class ValidationError(MacMindError):
    """
    数据验证错误
    
    输入参数验证失败、数据格式错误等情况。
    
    使用场景:
        - 用户输入为空或格式错误
        - 数据类型不匹配
        - 数据范围超出限制
        - 实体对象验证失败
    
    示例:
        raise ValidationError(
            "包名不能为空",
            field="package_name",
            value=""
        )
    """
    pass


class MacControlError(MacMindError):
    """
    Mac系统控制错误
    
    AppleScript执行失败、权限不足、应用不存在等情况。
    
    使用场景:
        - AppleScript执行失败
        - 应用程序不存在
        - 系统权限不足
        - 系统版本不兼容
    
    示例:
        raise MacControlError(
            "无法控制应用",
            app_name="网易云音乐",
            operation="quit",
            cause=applescript_error
        )
    """
    pass


class ConversationError(MacMindError):
    """
    会话管理错误
    
    会话创建、保存、加载失败等情况。
    
    使用场景:
        - 会话文件损坏
        - 会话数据序列化失败
        - 会话历史过长
        - Token估算错误
    
    示例:
        raise ConversationError(
            "会话保存失败",
            session_id="default",
            cause=io_error
        )
    """
    pass


def handle_exception(func):
    """
    异常处理装饰器
    
    自动捕获并转换标准异常为自定义异常。
    
    使用场景:
        装饰需要统一异常处理的函数
    
    示例:
        @handle_exception
        def some_function():
            # 函数逻辑
            pass
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MacMindError:
            raise
        except FileNotFoundError as e:
            raise ConfigError("文件不存在", cause=e)
        except PermissionError as e:
            raise ConfigError("权限不足", cause=e)
        except ValueError as e:
            raise ValidationError("数据验证失败", cause=e)
        except Exception as e:
            raise MacMindError(f"未知错误: {str(e)}", cause=e)
    
    return wrapper
