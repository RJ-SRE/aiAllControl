"""
测试自定义异常模块
"""

import pytest
from domain.exceptions import (
    MacMindError,
    ConfigError,
    BrewError,
    AIError,
    PackageError,
    ValidationError,
    MacControlError,
    ConversationError
)


def test_base_exception():
    """测试基础异常类"""
    error = MacMindError(
        "测试错误",
        detail="详细信息",
        context={'key': 'value'}
    )
    
    assert error.message == "测试错误"
    assert error.detail == "详细信息"
    assert error.context == {'key': 'value'}
    assert "测试错误" in str(error)
    assert "详细信息" in str(error)


def test_config_error():
    """测试配置错误"""
    error = ConfigError("API密钥未配置")
    
    assert isinstance(error, MacMindError)
    assert "API密钥未配置" in str(error)


def test_brew_error():
    """测试Homebrew错误"""
    error = BrewError(
        "安装失败",
        context={'package': 'vim', 'exit_code': 1}
    )
    
    assert isinstance(error, MacMindError)
    assert "安装失败" in str(error)


def test_ai_error():
    """测试AI服务错误"""
    error = AIError("AI推理失败", detail="网络超时")
    
    assert isinstance(error, MacMindError)
    assert "AI推理失败" in str(error)


def test_exception_with_context():
    """测试带上下文的异常"""
    error = PackageError(
        "软件包信息不完整",
        detail="缺少version字段",
        context={'package': 'vim', 'field': 'version'}
    )
    
    assert error.context['package'] == 'vim'
    assert error.context['field'] == 'version'
    assert "软件包信息不完整" in str(error)
