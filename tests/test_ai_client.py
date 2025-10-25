"""
AI客户端测试 - AI Client Tests

测试目标:
1. 抽象基类定义
2. 七牛云客户端功能
3. 工厂函数
4. 意图分析功能
5. 错误处理(不再降级)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from infrastructure.ai_client import AIClient, QiniuClient, create_ai_client


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


class TestQiniuClient:
    """测试七牛云客户端"""
    
    @patch('openai.OpenAI')
    def test_client_initialization(self, mock_openai):
        """测试客户端初始化"""
        client = QiniuClient('test_api_key')
        
        assert client is not None, "客户端应该能正常创建"
        mock_openai.assert_called_once_with(
            api_key='test_api_key',
            base_url='https://openai.qiniu.com/v1'
        )
    
    @patch('openai.OpenAI')
    def test_client_initialization_with_custom_params(self, mock_openai):
        """测试使用自定义参数初始化"""
        client = QiniuClient(
            'test_api_key',
            base_url='https://custom.endpoint.com/v1',
            model='gpt-3.5-turbo'
        )
        
        assert client is not None, "客户端应该能正常创建"
        assert client.model == 'gpt-3.5-turbo', "应该使用自定义模型"
        mock_openai.assert_called_once_with(
            api_key='test_api_key',
            base_url='https://custom.endpoint.com/v1'
        )
    
    def test_client_missing_library(self):
        """测试openai库未安装"""
        with patch.dict('sys.modules', {'openai': None}):
            with pytest.raises(RuntimeError, match="请安装OpenAI库"):
                QiniuClient('test_key')
    
    @patch('openai.OpenAI')
    def test_analyze_intent_success(self, mock_openai):
        """测试成功分析意图"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({
                'intent': '搜索',
                'keyword': '绘图软件',
                'category': '绘图'
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key')
        result = client.analyze_intent("帮我找一个绘图软件")
        
        assert result['intent'] == '搜索', "应该正确识别意图"
        assert result['keyword'] == '绘图软件', "应该正确提取关键词"
        assert result['category'] == '绘图', "应该正确识别类别"
    
    @patch('openai.OpenAI')
    def test_analyze_intent_with_error_raises_exception(self, mock_openai):
        """测试分析失败时抛出异常(不再降级)"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key')
        
        with pytest.raises(RuntimeError, match="AI模型推理失败"):
            client.analyze_intent("搜索vim")
    
    @patch('openai.OpenAI')
    def test_analyze_intent_calls_correct_model(self, mock_openai):
        """测试使用正确的模型"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"intent":"搜索","keyword":"test","category":""}'))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key', model='custom-model')
        client.analyze_intent("test")
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'custom-model', "应该使用自定义模型"
    
    @patch('openai.OpenAI')
    def test_analyze_intent_uses_json_format(self, mock_openai):
        """测试使用JSON格式响应"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"intent":"搜索","keyword":"test","category":""}'))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key')
        client.analyze_intent("test")
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['response_format'] == {"type": "json_object"}, "应该强制JSON输出"


class TestCreateAIClient:
    """测试工厂函数"""
    
    @patch('infrastructure.ai_client.config')
    @patch('openai.OpenAI')
    def test_create_qiniu_client(self, mock_openai, mock_config):
        """测试创建七牛云客户端"""
        mock_config.get.side_effect = lambda key, default=None: {
            'qiniu_api_key': 'test_key',
            'qiniu_base_url': 'https://openai.qiniu.com/v1',
            'qiniu_model': 'gpt-4'
        }.get(key, default)
        
        client = create_ai_client()
        
        assert isinstance(client, QiniuClient), "应该创建七牛云客户端"
    
    @patch('infrastructure.ai_client.config')
    def test_create_client_without_api_key(self, mock_config):
        """测试没有API密钥时抛出异常"""
        mock_config.get.return_value = None
        
        with pytest.raises(RuntimeError, match="未配置七牛云 API Key"):
            create_ai_client()
    
    @patch('infrastructure.ai_client.config')
    @patch('openai.OpenAI')
    def test_create_client_with_defaults(self, mock_openai, mock_config):
        """测试使用默认配置创建客户端"""
        def config_get(key, default=None):
            if key == 'qiniu_api_key':
                return 'test_key'
            return default
        
        mock_config.get.side_effect = config_get
        
        client = create_ai_client()
        
        assert isinstance(client, QiniuClient), "应该创建七牛云客户端"
        mock_openai.assert_called_once()


class TestAIClientIntegration:
    """测试集成场景"""
    
    @patch('openai.OpenAI')
    def test_full_workflow(self, mock_openai):
        """测试完整工作流程"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({
                'intent': '搜索',
                'keyword': 'vim',
                'category': '编辑器'
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key')
        
        result = client.analyze_intent("帮我找一个像vim的编辑器")
        
        assert 'intent' in result, "结果应该包含意图"
        assert 'keyword' in result, "结果应该包含关键词"
        assert 'category' in result, "结果应该包含类别"
    
    @patch('openai.OpenAI')
    def test_error_stops_execution(self, mock_openai):
        """测试错误时停止执行(需求4)"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Network Error")
        mock_openai.return_value = mock_client
        
        client = QiniuClient('test_key')
        
        with pytest.raises(RuntimeError):
            client.analyze_intent("测试输入")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
