"""
Homebrew执行器测试 - Brew Executor Tests

测试目标:
1. 命令执行基础功能
2. 搜索功能
3. 获取包信息功能
4. 安装功能
5. 列出已安装包功能
6. 错误处理
7. 超时控制
"""

import pytest
import subprocess
import json
from unittest.mock import Mock, patch, MagicMock
from infrastructure.brew_executor import BrewExecutor, brew


class TestBrewExecutorInit:
    """测试初始化"""
    
    def test_executor_created(self):
        """测试执行器能正常创建"""
        executor = BrewExecutor()
        assert executor is not None, "执行器应该能正常创建"
    
    def test_brew_path_from_config(self):
        """测试Homebrew路径从配置读取"""
        executor = BrewExecutor()
        assert executor.brew_path is not None, "应该有Homebrew路径配置"
    
    def test_module_level_brew_instance(self):
        """测试模块级brew实例存在"""
        assert brew is not None, "模块级brew实例应该存在"


class TestBrewExecutorExecute:
    """测试命令执行"""
    
    @patch('subprocess.run')
    def test_execute_success(self, mock_run):
        """测试成功执行命令"""
        mock_run.return_value = Mock(stdout="test output", returncode=0)
        
        executor = BrewExecutor()
        result = executor._execute(['--version'])
        
        assert result == "test output", "应该返回命令输出"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_execute_with_timeout(self, mock_run):
        """测试带超时的命令执行"""
        mock_run.return_value = Mock(stdout="output", returncode=0)
        
        executor = BrewExecutor()
        executor._execute(['search', 'vim'], timeout=60)
        
        args, kwargs = mock_run.call_args
        assert kwargs['timeout'] == 60, "应该使用指定的超时时间"
    
    @patch('subprocess.run')
    def test_execute_failure(self, mock_run):
        """测试命令执行失败"""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, 
            cmd='brew',
            stderr='Error message'
        )
        
        executor = BrewExecutor()
        with pytest.raises(RuntimeError):
            executor._execute(['invalid', 'command'])
    
    @patch('subprocess.run')
    def test_execute_timeout_expired(self, mock_run):
        """测试命令超时"""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd='brew',
            timeout=1
        )
        
        executor = BrewExecutor()
        with pytest.raises(RuntimeError):
            executor._execute(['search', 'test'], timeout=1)


class TestBrewExecutorSearch:
    """测试搜索功能"""
    
    @patch('subprocess.run')
    def test_search_returns_list(self, mock_run):
        """测试搜索返回列表"""
        mock_run.return_value = Mock(
            stdout="vim\nvim-go\nneovim\n",
            returncode=0
        )
        
        executor = BrewExecutor()
        results = executor.search('vim')
        
        assert isinstance(results, list), "应该返回列表"
        assert len(results) == 3, "应该返回3个结果"
        assert 'vim' in results, "结果中应该包含vim"
    
    @patch('subprocess.run')
    def test_search_filters_empty_lines(self, mock_run):
        """测试搜索过滤空行"""
        mock_run.return_value = Mock(
            stdout="vim\n\nneovim\n\n",
            returncode=0
        )
        
        executor = BrewExecutor()
        results = executor.search('vim')
        
        assert len(results) == 2, "应该过滤掉空行"
    
    @patch('subprocess.run')
    def test_search_with_keyword(self, mock_run):
        """测试带关键词搜索"""
        mock_run.return_value = Mock(stdout="drawing\n", returncode=0)
        
        executor = BrewExecutor()
        executor.search('drawing')
        
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert 'search' in cmd, "命令中应该包含search"
        assert 'drawing' in cmd, "命令中应该包含搜索关键词"


class TestBrewExecutorInfo:
    """测试获取包信息功能"""
    
    @patch('subprocess.run')
    def test_info_formula_package(self, mock_run):
        """测试获取Formula包信息"""
        mock_output = json.dumps({
            'formulae': [{
                'name': 'wget',
                'desc': 'Internet file retriever',
                'version': '1.21.4'
            }],
            'casks': []
        })
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)
        
        executor = BrewExecutor()
        info = executor.info('wget')
        
        assert info['name'] == 'wget', "应该返回包信息"
        assert 'desc' in info, "应该包含描述"
    
    @patch('subprocess.run')
    def test_info_cask_package(self, mock_run):
        """测试获取Cask包信息"""
        mock_output = json.dumps({
            'formulae': [],
            'casks': [{
                'name': 'drawio',
                'desc': 'Draw.io desktop',
                'version': '24.7.8'
            }]
        })
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)
        
        executor = BrewExecutor()
        info = executor.info('drawio')
        
        assert info['name'] == 'drawio', "应该返回Cask包信息"
    
    @patch('subprocess.run')
    def test_info_package_not_found(self, mock_run):
        """测试包不存在"""
        mock_output = json.dumps({'formulae': [], 'casks': []})
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)
        
        executor = BrewExecutor()
        with pytest.raises(RuntimeError):
            executor.info('nonexistent-package')


class TestBrewExecutorInstall:
    """测试安装功能"""
    
    @patch('subprocess.run')
    def test_install_formula(self, mock_run):
        """测试安装Formula包"""
        mock_run.return_value = Mock(stdout="Success", returncode=0)
        
        executor = BrewExecutor()
        result = executor.install('wget', is_cask=False)
        
        assert result is True, "安装应该成功"
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert 'install' in cmd, "命令中应该包含install"
        assert '--cask' not in cmd, "不应该包含--cask参数"
    
    @patch('subprocess.run')
    def test_install_cask(self, mock_run):
        """测试安装Cask包"""
        mock_run.return_value = Mock(stdout="Success", returncode=0)
        
        executor = BrewExecutor()
        result = executor.install('drawio', is_cask=True)
        
        assert result is True, "安装应该成功"
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert '--cask' in cmd, "应该包含--cask参数"
    
    @patch('subprocess.run')
    def test_install_failure(self, mock_run):
        """测试安装失败"""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd='brew',
            stderr='Install failed'
        )
        
        executor = BrewExecutor()
        result = executor.install('invalid-package')
        
        assert result is False, "安装失败应该返回False"
    
    @patch('subprocess.run')
    def test_install_timeout(self, mock_run):
        """测试安装使用较长超时"""
        mock_run.return_value = Mock(stdout="Success", returncode=0)
        
        executor = BrewExecutor()
        executor.install('wget')
        
        args, kwargs = mock_run.call_args
        assert kwargs['timeout'] == 300, "安装命令应该使用300秒超时"


class TestBrewExecutorListInstalled:
    """测试列出已安装包功能"""
    
    @patch('subprocess.run')
    def test_list_installed(self, mock_run):
        """测试列出已安装包"""
        mock_run.return_value = Mock(
            stdout="wget\ncurl\ngit\n",
            returncode=0
        )
        
        executor = BrewExecutor()
        installed = executor.list_installed()
        
        assert isinstance(installed, list), "应该返回列表"
        assert 'wget' in installed, "结果中应该包含已安装的包"
        assert len(installed) == 3, "应该返回3个包"
    
    @patch('subprocess.run')
    def test_list_installed_empty(self, mock_run):
        """测试没有已安装包的情况"""
        mock_run.return_value = Mock(stdout="", returncode=0)
        
        executor = BrewExecutor()
        installed = executor.list_installed()
        
        assert installed == [], "应该返回空列表"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
