"""
集成测试 - Integration Tests

测试完整的业务流程和模块间交互。

测试场景:
1. 完整的软件搜索流程
2. 软件包信息获取流程
3. AI对话流程(mock)
4. Mac控制流程(mock)
5. 会话管理流程

设计说明:
- 使用pytest fixture提供测试环境
- 使用mock模拟外部依赖(AI API, Homebrew, AppleScript)
- 测试真实的业务逻辑流程
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from service.package_service import PackageService
from repository.package_repository import PackageRepository
from domain.package import Package, PackageType, LicenseType
from infrastructure.conversation import ConversationManager
from infrastructure.mac_controller import MacController
from controller.cli_controller import CLIController


class TestPackageSearchIntegration:
    """
    软件包搜索集成测试
    
    测试完整的搜索流程: 用户输入 → AI分析 → 搜索 → 排序 → 返回结果
    """
    
    @patch('infrastructure.brew_executor.brew.search')
    @patch('infrastructure.brew_executor.brew.info')
    @patch('infrastructure.ai_client.create_ai_client')
    def test_complete_search_flow(self, mock_ai, mock_info, mock_search):
        """
        测试完整的搜索流程
        
        模拟:
        1. AI分析用户输入
        2. Homebrew搜索软件包
        3. 获取软件包详细信息
        4. 排序和返回结果
        """
        mock_ai_instance = Mock()
        mock_ai_instance.analyze_intent.return_value = {
            'intent': '搜索',
            'keyword': '绘图',
            'category': '绘图'
        }
        mock_ai.return_value = mock_ai_instance
        
        mock_search.return_value = ['drawio', 'krita']
        
        mock_info.side_effect = [
            {
                'name': 'drawio',
                'desc': 'Diagram editor',
                'version': '21.0.0',
                'license': 'Apache-2.0',
                'homepage': 'https://draw.io'
            },
            {
                'name': 'krita',
                'desc': 'Digital painting',
                'version': '5.0.0',
                'license': 'GPL-3.0',
                'homepage': 'https://krita.org'
            }
        ]
        
        service = PackageService()
        result = service.search_packages("帮我找一个绘图软件")
        
        assert result.keyword == '绘图'
        assert result.intent == '搜索'
        assert len(result.packages) == 2
        assert result.packages[0].name in ['drawio', 'krita']
        
        mock_ai_instance.analyze_intent.assert_called_once()
        mock_search.assert_called_once_with('绘图')


class TestConversationIntegration:
    """
    对话管理集成测试
    
    测试会话管理的完整流程
    """
    
    def test_conversation_flow(self, tmp_path):
        """
        测试对话流程: 添加消息 → 获取上下文 → 保存会话 → 加载会话
        """
        manager = ConversationManager()
        manager.session_dir = tmp_path
        manager.clear_history()
        
        manager.add_user_message("帮我找一个绘图软件")
        manager.add_assistant_message("我推荐drawio")
        manager.add_user_message("如何安装")
        manager.add_assistant_message("执行 brew install drawio")
        
        assert manager.get_message_count() == 4
        assert manager.get_conversation_turns() == 2
        
        context = manager.get_context(max_messages=4)
        assert len(context) == 4
        assert context[0]['role'] == 'user'
        assert context[0]['content'] == '帮我找一个绘图软件'
        
        manager.save_session("test_session")
        session_file = tmp_path / "test_session_session.json"
        assert session_file.exists()
        
        manager.clear_history()
        assert manager.get_message_count() == 0
        
        manager.load_session("test_session")
        assert manager.get_message_count() == 4
        assert manager.get_conversation_turns() == 2


class TestMacControlIntegration:
    """
    Mac控制集成测试
    
    测试Mac系统控制的流程(使用mock)
    """
    
    @patch('infrastructure.mac_controller.platform.system')
    @patch('infrastructure.mac_controller.subprocess.run')
    def test_app_control_flow(self, mock_run, mock_system):
        """
        测试应用控制流程: 打开应用 → 查询状态 → 关闭应用
        """
        mock_system.return_value = 'Darwin'
        
        mock_result = Mock()
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        
        controller = MacController()
        
        controller.open_app("Safari")
        mock_run.assert_called()
        
        mock_result.stdout = 'true'
        is_running = controller.is_app_running("Safari")
        assert is_running == True
        
        controller.quit_app("Safari")
        mock_run.assert_called()


class TestCLIIntegration:
    """
    CLI集成测试
    
    测试命令行界面的完整流程
    """
    
    @patch('infrastructure.brew_executor.brew.search')
    @patch('infrastructure.brew_executor.brew.info')
    @patch('builtins.print')
    def test_cli_search_command(self, mock_print, mock_info, mock_search):
        """
        测试CLI搜索命令的完整流程
        """
        mock_search.return_value = ['vim']
        mock_info.return_value = {
            'name': 'vim',
            'desc': 'Vi IMproved',
            'version': '9.0',
            'license': 'Vim',
            'homepage': 'https://vim.org'
        }
        
        controller = CLIController()
        controller.run(['search', 'vim'])
        
        mock_search.assert_called_once()
        mock_print.assert_called()


class TestEndToEndFlow:
    """
    端到端流程测试
    
    测试从用户输入到最终输出的完整流程
    """
    
    @patch('infrastructure.brew_executor.brew')
    @patch('infrastructure.ai_client.create_ai_client')
    def test_search_to_result_flow(self, mock_ai, mock_brew):
        """
        测试完整的搜索到结果流程
        
        流程:
        1. 用户输入自然语言查询
        2. AI分析意图和关键词
        3. Repository搜索软件包
        4. 获取软件包详细信息
        5. Service层排序和过滤
        6. 返回结果给Controller
        """
        mock_ai_instance = Mock()
        mock_ai_instance.analyze_intent.return_value = {
            'intent': '搜索',
            'keyword': 'editor',
            'category': '编辑器'
        }
        mock_ai.return_value = mock_ai_instance
        
        mock_brew.search.return_value = ['vim', 'emacs']
        mock_brew.info.side_effect = [
            {
                'name': 'vim',
                'desc': 'Vi IMproved',
                'version': '9.0',
                'license': 'Vim',
                'homepage': 'https://vim.org'
            },
            {
                'name': 'emacs',
                'desc': 'GNU Emacs',
                'version': '29.0',
                'license': 'GPL-3.0',
                'homepage': 'https://gnu.org/software/emacs'
            }
        ]
        mock_brew.list_installed.return_value = []
        
        service = PackageService()
        result = service.search_packages("帮我找一个编辑器")
        
        assert result.total_count == 2
        assert result.keyword == 'editor'
        assert len(result.packages) == 2
        
        for pkg in result.packages:
            assert isinstance(pkg, Package)
            assert pkg.name in ['vim', 'emacs']


class TestNotificationIntegration:
    """
    通知管理集成测试
    
    测试通知相关功能的完整流程
    """
    
    @patch('infrastructure.mac_controller.platform.system')
    @patch('infrastructure.mac_controller.subprocess.run')
    def test_notification_send_flow(self, mock_run, mock_system):
        """
        测试发送通知流程
        """
        mock_system.return_value = 'Darwin'
        mock_result = Mock()
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        
        controller = MacController()
        success = controller.send_notification(
            "测试标题",
            "测试消息",
            subtitle="测试副标题"
        )
        
        assert success == True
        mock_run.assert_called()
    
    @patch('infrastructure.mac_controller.platform.system')
    def test_notification_settings_guide(self, mock_system):
        """
        测试通知设置引导流程
        """
        mock_system.return_value = 'Darwin'
        
        controller = MacController()
        guide = controller.enable_app_notifications("Safari")
        
        assert "Safari" in guide
        assert "通知" in guide
        assert "步骤" in guide


class TestShortcutIntegration:
    """
    快捷键管理集成测试
    
    测试快捷键相关功能的完整流程
    """
    
    @patch('infrastructure.mac_controller.platform.system')
    def test_shortcut_guide_generation(self, mock_system):
        """
        测试快捷键引导生成
        """
        mock_system.return_value = 'Darwin'
        
        controller = MacController()
        guide = controller.create_keyboard_shortcut_guide(
            "Command+Shift+L",
            "打开工作应用",
            ["企业微信", "WPS"]
        )
        
        assert "Command+Shift+L" in guide
        assert "打开工作应用" in guide
        assert "企业微信" in guide
        assert "WPS" in guide
        assert "Automator" in guide or "Hammerspoon" in guide
    
    @patch('infrastructure.mac_controller.platform.system')
    def test_shortcut_conflict_check(self, mock_system):
        """
        测试快捷键冲突检查
        """
        mock_system.return_value = 'Darwin'
        
        controller = MacController()
        
        result = controller.check_keyboard_shortcut_conflicts("Command+L")
        assert result['has_conflict'] == True
        assert "锁定屏幕" in result['conflicts_with']
        
        result = controller.check_keyboard_shortcut_conflicts("Command+Shift+L")
        assert result['has_conflict'] == False


class TestConversationPromptIntegration:
    """
    对话提示词集成测试
    
    测试优化后的提示词功能
    """
    
    def test_optimized_prompt_generation(self):
        """
        测试优化后的系统提示词生成
        """
        manager = ConversationManager()
        prompt = manager.get_optimized_system_prompt()
        
        assert "MacMind" in prompt
        assert "软件管理" in prompt
        assert "系统控制" in prompt
        assert "通知" in prompt
        assert "快捷键" in prompt
    
    def test_context_with_summary(self, tmp_path):
        """
        测试带总结的上下文生成
        """
        manager = ConversationManager()
        manager.session_dir = tmp_path
        manager.clear_history()
        
        for i in range(10):
            manager.add_user_message(f"搜索软件 {i}")
            manager.add_assistant_message(f"找到软件 {i}")
        
        context = manager.get_context_with_summary(max_messages=5)
        
        assert len(context) > 0
        assert any("总结" in msg.get("content", "") for msg in context)
    
    def test_topic_extraction(self, tmp_path):
        """
        测试主题提取功能
        """
        manager = ConversationManager()
        manager.session_dir = tmp_path
        manager.clear_history()
        
        manager.add_user_message("帮我搜索绘图软件")
        manager.add_user_message("打开Safari")
        manager.add_user_message("关闭通知")
        
        messages = manager.get_context()
        topics = manager._extract_topics(messages)
        
        assert "软件" in topics or "系统控制" in topics or "通知管理" in topics


class TestAdvancedIntegrationScenarios:
    """
    高级集成测试场景
    
    测试复杂的业务流程组合
    """
    
    @patch('infrastructure.brew_executor.brew')
    @patch('infrastructure.mac_controller.subprocess.run')
    @patch('infrastructure.mac_controller.platform.system')
    def test_install_and_notify_flow(self, mock_system, mock_subprocess, mock_brew):
        """
        测试安装软件后发送通知的完整流程
        """
        mock_system.return_value = 'Darwin'
        mock_subprocess_result = Mock()
        mock_subprocess_result.stdout = ''
        mock_subprocess_result.stderr = ''
        mock_subprocess.return_value = mock_subprocess_result
        
        mock_brew.search.return_value = ['drawio']
        mock_brew.info.return_value = {
            'name': 'drawio',
            'desc': 'Diagram editor',
            'version': '21.0.0',
            'license': 'Apache-2.0'
        }
        mock_brew.install.return_value = True
        
        service = PackageService()
        mac_controller = MacController()
        
        success = service.install_package('drawio')
        assert success == True
        
        notification_sent = mac_controller.send_notification(
            "MacMind",
            "软件安装完成",
            subtitle="drawio 已成功安装"
        )
        assert notification_sent == True
    
    @patch('infrastructure.mac_controller.platform.system')
    def test_conversation_with_context(self, mock_system, tmp_path):
        """
        测试带上下文的多轮对话流程
        """
        mock_system.return_value = 'Darwin'
        
        manager = ConversationManager()
        manager.session_dir = tmp_path
        manager.clear_history()
        
        manager.add_user_message("帮我找一个绘图软件")
        manager.add_assistant_message("我推荐drawio")
        manager.add_context_message("用户对drawio感兴趣")
        manager.add_user_message("如何安装")
        manager.add_assistant_message("执行 brew install drawio")
        
        context = manager.get_context()
        
        assert len(context) == 5
        assert any("[上下文]" in msg.get("content", "") for msg in context)
        
        turns = manager.get_conversation_turns()
        assert turns == 2


@pytest.fixture
def temp_session_dir(tmp_path):
    """提供临时会话目录"""
    return tmp_path


@pytest.fixture
def clean_conversation_manager(temp_session_dir):
    """提供干净的会话管理器"""
    manager = ConversationManager()
    manager.session_dir = temp_session_dir
    manager.clear_history()
    yield manager
    manager.clear_history()
