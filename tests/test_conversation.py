"""
测试会话管理模块
"""

import pytest
from infrastructure.conversation import ConversationManager


@pytest.fixture
def conversation():
    """创建会话管理器实例"""
    manager = ConversationManager(max_history=10)
    manager.clear()
    return manager


def test_add_user_message(conversation):
    """测试添加用户消息"""
    conversation.add_user_message("帮我找一个绘图软件")
    
    assert conversation.get_message_count() == 1
    context = conversation.get_context()
    assert len(context) == 1
    assert context[0]['role'] == 'user'
    assert context[0]['content'] == "帮我找一个绘图软件"


def test_add_assistant_message(conversation):
    """测试添加助手消息"""
    conversation.add_assistant_message("我推荐使用drawio")
    
    assert conversation.get_message_count() == 1
    context = conversation.get_context()
    assert context[0]['role'] == 'assistant'


def test_add_system_message(conversation):
    """测试添加系统消息"""
    conversation.add_system_message("你是一个软件包管理助手")
    
    assert conversation.get_message_count() == 1
    context = conversation.get_context()
    assert context[0]['role'] == 'system'


def test_get_context_with_limit(conversation):
    """测试获取有限数量的上下文"""
    for i in range(15):
        conversation.add_user_message(f"消息 {i}")
    
    context = conversation.get_context(max_messages=5)
    assert len(context) == 5


def test_clear_history(conversation):
    """测试清空历史"""
    conversation.add_user_message("测试消息")
    conversation.clear()
    
    assert conversation.get_message_count() == 0


def test_get_last_messages(conversation):
    """测试获取最后的消息"""
    conversation.add_user_message("用户消息")
    conversation.add_assistant_message("助手消息")
    
    assert conversation.get_last_user_message() == "用户消息"
    assert conversation.get_last_assistant_message() == "助手消息"


def test_estimate_tokens(conversation):
    """测试估算tokens"""
    conversation.add_user_message("这是一条测试消息")
    
    tokens = conversation.estimate_tokens()
    assert tokens > 0


def test_trim_history(conversation):
    """测试历史记录修剪"""
    manager = ConversationManager(max_history=5)
    manager.clear()
    
    for i in range(10):
        manager.add_user_message(f"消息 {i}")
    
    assert manager.get_message_count() <= 5
