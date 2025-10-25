"""
AI客户端测试 - AI Client Tests

测试目标:
1. 抽象基类定义
2. Anthropic客户端功能
3. OpenAI客户端功能
4. 工厂函数
5. 意图分析功能
6. 错误处理和降级
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from infrastructure.ai_client import AIClient, AnthropicClient, OpenAIClient, create_ai_client


class TestAIClientAbstract:
    """测试抽象基类"""
    
    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            AIClient()
    
    def test_subclass_must_implement_analyze_intent(self):
        """测试子类必须实现analyze_intent方法"""
        class IncompleteClient(AIClient):
            pass
        
        with pytest.raises(TypeError):
            IncompleteClient()


class TestAnthropicClient:
    """测试Anthropic客户端"""
    
    @patch('anthropic.Anthropic')
    def test_client_initialization(self, mock_anthropic):
        """测试客户端初始化"""
        client = AnthropicClient('test_api_key')
        
        assert client is not None, "客户端应该能正常创建"
        mock_anthropic.assert_called_once_with(api_key='test_api_key')
    
    def test_client_missing_library(self):
        """测试anthropic库未安装"""
        with patch.dict('sys.modules', {'anthropic': None}):
            with pytest.raises(RuntimeError, match="请安装Anthropic库"):
                AnthropicClient('test_key')
    
    @patch('anthropic.Anthropic')
    def test_analyze_intent_success(self, mock_anthropic):
        """测试成功分析意图"""
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps({
            'intent': '搜索',
            'keyword': '绘图软件',
            'category': '绘图'
        }))]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        client = AnthropicClient('test_key')
        result = client.analyze_intent("帮我找一个绘图软件")
        
        assert result['intent'] == '搜索', "应该正确识别意图"
        assert result['keyword'] == '绘图软件', "应该正确提取关键词"
        assert result['category'] == '绘图', "应该正确识别类别"
    
    @patch('anthropic.Anthropic')
    def test_analyze_intent_with_error_fallback(self, mock_anthropic):
        """测试分析失败时的降级处理"""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        client = AnthropicClient('test_key')
        result = client.analyze_intent("搜索vim")
        
        assert result['intent'] == '搜索', "降级后应该返回默认意图"
        assert result['keyword'] == '搜索vim', "降级后应该使用原始输入作为关键词"
        assert result['category'] == '', "降级后类别为空"
    
    @patch('anthropic.Anthropic')
    def test_analyze_intent_calls_correct_model(self, mock_anthropic):
        """测试使用正确的模型"""
        mock_message = Mock()
        mock_message.content = [Mock(text='{"intent":"搜索","keyword":"test","category":""}')]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        client = AnthropicClient('test_key')
        client.analyze_intent("test")
        
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == 'claude-3-5-sonnet-20241022', "应该使用正确的模型"


class TestOpenAIClient:
    """测试OpenAI客户端"""
    
    @patch('openai.OpenAI')
    def test_client_initialization(self, mock_openai):
        """测试客户端初始化"""
        client = OpenAIClient('test_api_key')
        
        assert client is not None, "客户端应该能正常创建"
        mock_openai.assert_called_once_with(api_key='test_api_key')
    
    def test_client_missing_library(self):
        """测试openai库未安装"""
        with patch.dict('sys.modules', {'openai': None}):
            with pytest.raises(RuntimeError, match="请安装OpenAI库"):
                OpenAIClient('test_key')
    
    @patch('openai.OpenAI')
    def test_analyze_intent_success(self, mock_openai):
        """测试成功分析意图"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({
                'intent': '安装',
                'keyword': '编辑器',
                'category': '编程'
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = OpenAIClient('test_key')
        result = client.analyze_intent("安装一个编辑器")
        
        assert result['intent'] == '安装', "应该正确识别意图"
        assert result['keyword'] == '编辑器', "应该正确提取关键词"
    
    @patch('openai.OpenAI')
    def test_analyze_intent_with_error_fallback(self, mock_openai):
        """测试分析失败时的降级处理"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        client = OpenAIClient('test_key')
        result = client.analyze_intent("测试输入")
        
        assert result['intent'] == '搜索', "降级后应该返回默认意图"
        assert result['keyword'] == '测试输入', "降级后应该使用原始输入"


class TestCreateAIClient:
    """测试工厂函数"""
    
    @patch('infrastructure.ai_client.config')
    @patch('anthropic.Anthropic')
    def test_create_anthropic_client(self, mock_anthropic, mock_config):
        """测试创建Anthropic客户端"""
        mock_config.get.side_effect = lambda key, default=None: {
            'api_key': 'test_key',
            'api_provider': 'anthropic'
        }.get(key, default)
        
        client = create_ai_client()
        
        assert isinstance(client, AnthropicClient), "应该创建Anthropic客户端"
    
    @patch('infrastructure.ai_client.config')
    @patch('openai.OpenAI')
    def test_create_openai_client(self, mock_openai, mock_config):
        """测试创建OpenAI客户端"""
        mock_config.get.side_effect = lambda key, default=None: {
            'api_key': 'test_key',
            'api_provider': 'openai'
        }.get(key, default)
        
        client = create_ai_client()
        
        assert isinstance(client, OpenAIClient), "应该创建OpenAI客户端"
    
    @patch('infrastructure.ai_client.config')
    def test_create_client_without_api_key(self, mock_config):
        """测试没有API密钥时抛出异常"""
        mock_config.get.return_value = None
        
        with pytest.raises(RuntimeError, match="未配置API Key"):
            create_ai_client()
    
    @patch('infrastructure.ai_client.config')
    def test_create_client_with_unsupported_provider(self, mock_config):
        """测试不支持的AI提供商"""
        mock_config.get.side_effect = lambda key, default=None: {
            'api_key': 'test_key',
            'api_provider': 'unsupported'
        }.get(key, default)
        
        with pytest.raises(ValueError, match="不支持的AI提供商"):
            create_ai_client()


class TestAIClientIntegration:
    """测试集成场景"""
    
    @patch('anthropic.Anthropic')
    def test_full_workflow(self, mock_anthropic):
        """测试完整工作流程"""
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps({
            'intent': '搜索',
            'keyword': 'vim',
            'category': '编辑器'
        }))]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        client = AnthropicClient('test_key')
        
        result = client.analyze_intent("帮我找一个像vim的编辑器")
        
        assert 'intent' in result, "结果应该包含意图"
        assert 'keyword' in result, "结果应该包含关键词"
        assert 'category' in result, "结果应该包含类别"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
