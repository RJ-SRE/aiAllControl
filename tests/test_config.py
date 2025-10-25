"""
配置管理模块测试 - Config Module Tests

测试目标:
1. 单例模式是否正常工作
2. 默认配置是否正确
3. 配置读取和设置是否正常
4. 配置文件保存和加载是否正常
5. 环境变量优先级是否正确
6. 配置验证是否正常工作
"""

import pytest
import os
import json
from pathlib import Path
from infrastructure.config import Config, config


class TestConfigSingleton:
    """测试单例模式"""
    
    def test_singleton_same_instance(self):
        """测试多次创建返回同一实例"""
        config1 = Config()
        config2 = Config()
        assert config1 is config2, "应该返回同一个实例"
    
    def test_module_level_config_is_singleton(self):
        """测试模块级config是单例实例"""
        new_config = Config()
        assert config is new_config, "模块级config应该是单例实例"


class TestConfigDefaults:
    """测试默认配置"""
    
    def test_default_api_provider(self):
        """测试默认AI提供商"""
        assert config.get('api_provider') == 'anthropic', "默认应该使用anthropic"
    
    def test_default_homebrew_path(self):
        """测试默认Homebrew路径"""
        expected_path = '/opt/homebrew/bin/brew'
        assert config.get('homebrew_path') == expected_path, "默认路径应该是Apple Silicon Mac路径"
    
    def test_default_max_search_results(self):
        """测试默认最大搜索结果数"""
        assert config.get('max_search_results') == 5, "默认应该显示5个结果"
    
    def test_default_auto_install(self):
        """测试默认自动安装设置"""
        assert config.get('auto_install') is False, "默认不应该自动安装"
    
    def test_default_preferred_licenses(self):
        """测试默认许可证偏好"""
        licenses = config.get('preferred_license')
        assert 'MIT' in licenses, "应该包含MIT许可证"
        assert 'Apache-2.0' in licenses, "应该包含Apache-2.0许可证"
        assert 'GPL-3.0' in licenses, "应该包含GPL-3.0许可证"
    
    def test_default_cache_ttl(self):
        """测试默认缓存有效期"""
        assert config.get('cache_ttl') == 3600, "默认缓存应该是1小时(3600秒)"


class TestConfigGetSet:
    """测试配置读取和设置"""
    
    def test_get_existing_key(self):
        """测试获取存在的配置项"""
        value = config.get('api_provider')
        assert value is not None, "应该能获取到配置值"
    
    def test_get_nonexistent_key_with_default(self):
        """测试获取不存在的配置项(带默认值)"""
        value = config.get('nonexistent_key', 'default_value')
        assert value == 'default_value', "应该返回默认值"
    
    def test_get_nonexistent_key_without_default(self):
        """测试获取不存在的配置项(不带默认值)"""
        value = config.get('nonexistent_key')
        assert value is None, "应该返回None"
    
    def test_set_and_get(self):
        """测试设置和获取配置"""
        config.set('test_key', 'test_value')
        assert config.get('test_key') == 'test_value', "应该能获取到设置的值"


class TestConfigPersistence:
    """测试配置持久化"""
    
    def test_config_directory_created(self):
        """测试配置目录创建"""
        config_dir = Path.home() / '.macmind'
        config.save()
        assert config_dir.exists(), "配置目录应该被创建"
    
    def test_config_file_saved(self):
        """测试配置文件保存"""
        config_file = Path.home() / '.macmind' / 'config.json'
        config.save()
        assert config_file.exists(), "配置文件应该被创建"
    
    def test_api_key_not_saved_to_file(self):
        """测试API密钥不保存到文件"""
        config.set('api_key', 'test_secret_key')
        config.save()
        
        config_file = Path.home() / '.macmind' / 'config.json'
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert 'api_key' not in saved_config, "API密钥不应该保存到文件中"
    
    def test_config_file_is_json(self):
        """测试配置文件是有效的JSON"""
        config.save()
        config_file = Path.home() / '.macmind' / 'config.json'
        
        try:
            with open(config_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            pytest.fail("配置文件应该是有效的JSON格式")


class TestConfigValidation:
    """测试配置验证"""
    
    def test_validate_without_api_key(self):
        """测试没有API密钥时验证失败"""
        test_config = Config()
        test_config._config['api_key'] = None
        assert not test_config.validate(), "没有API密钥应该验证失败"
    
    def test_validate_with_invalid_homebrew_path(self):
        """测试Homebrew路径无效时验证失败"""
        test_config = Config()
        test_config._config['api_key'] = 'test_key'
        test_config._config['homebrew_path'] = '/nonexistent/path/brew'
        assert not test_config.validate(), "Homebrew路径不存在应该验证失败"


class TestConfigEnvironmentVariables:
    """测试环境变量支持"""
    
    def test_anthropic_api_key_from_env(self, monkeypatch):
        """测试从ANTHROPIC_API_KEY环境变量读取"""
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test_anthropic_key')
        test_config = Config()
        test_config._load_config()
        assert test_config.get('api_key') == 'test_anthropic_key', "应该从环境变量读取API密钥"
    
    def test_openai_api_key_from_env(self, monkeypatch):
        """测试从OPENAI_API_KEY环境变量读取"""
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')
        test_config = Config()
        test_config._load_config()
        assert test_config.get('api_key') == 'test_openai_key', "应该从环境变量读取API密钥"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
