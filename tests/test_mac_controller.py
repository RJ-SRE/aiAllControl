"""
测试Mac系统控制模块

注意: 这些测试需要在macOS环境中运行
"""

import pytest
import platform
from infrastructure.mac_controller import MacController


pytestmark = pytest.mark.skipif(
    platform.system() != 'Darwin',
    reason="Mac控制器测试需要在macOS环境中运行"
)


@pytest.fixture
def controller():
    """创建Mac控制器实例"""
    return MacController()


def test_get_macos_version(controller):
    """测试获取macOS版本"""
    version = controller.get_macos_version()
    
    if version:
        assert isinstance(version, str)
        assert len(version) > 0


def test_get_running_apps(controller):
    """测试获取运行中的应用"""
    apps = controller.get_running_apps()
    
    assert isinstance(apps, list)


def test_is_app_running(controller):
    """测试检查应用是否运行"""
    result = controller.is_app_running("Finder")
    assert isinstance(result, bool)


def test_singleton_pattern():
    """测试单例模式"""
    controller1 = MacController()
    controller2 = MacController()
    
    assert controller1 is controller2
