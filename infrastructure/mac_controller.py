"""
Mac系统控制模块 - Mac Controller

通过AppleScript和系统命令控制macOS应用和系统设置。

设计模式: 单例模式 + 命令模式
- 单例模式: 确保全局只有一个Mac控制器
- 命令模式: 封装系统操作为独立命令

核心功能:
1. 应用控制 - 打开、关闭、查询应用状态
2. 通知管理 - 启用、禁用应用通知权限
3. 快捷键设置 - 配置全局快捷键(需要第三方工具)
4. 系统信息 - 查询macOS版本、应用信息等

使用示例:
    from infrastructure.mac_controller import mac_controller
    
    # 关闭应用
    mac_controller.quit_app("网易云音乐")
    
    # 打开应用
    mac_controller.open_app("Safari")
    
    # 禁用通知
    mac_controller.disable_notifications("com.netease.163music")
"""

import subprocess
from typing import Optional, List
from infrastructure.logger import logger
from domain.exceptions import MacControlError


class MacController:
    """
    Mac系统控制器 - 单例模式实现
    
    属性:
        _instance: 类级别的单例实例
        _initialized: 标记是否已初始化
    
    设计说明:
        采用单例模式确保全局只有一个Mac控制器,
        避免重复的系统调用和资源浪费。
    """
    
    _instance: Optional['MacController'] = None
    
    def __new__(cls):
        """
        控制对象创建,实现单例模式
        
        返回:
            MacController: 全局唯一的Mac控制器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化Mac控制器
        
        说明:
            使用_initialized标志避免重复初始化
        """
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.debug("MacController初始化完成")
    
    def _execute_applescript(self, script: str) -> str:
        """
        执行AppleScript脚本
        
        参数:
            script: AppleScript脚本内容
        
        返回:
            str: 脚本输出
        
        抛出:
            MacControlError: 脚本执行失败
        
        说明:
            使用osascript命令执行AppleScript
        """
        try:
            logger.debug(f"执行AppleScript: {script[:100]}...")
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript执行失败: {e.stderr}")
            raise MacControlError(
                "AppleScript执行失败",
                detail=e.stderr,
                context={'script': script[:100]}
            )
        except subprocess.TimeoutExpired:
            logger.error("AppleScript执行超时")
            raise MacControlError(
                "AppleScript执行超时",
                detail="脚本执行超过30秒",
                context={'script': script[:100]}
            )
        except Exception as e:
            logger.error(f"AppleScript执行异常: {e}", exc_info=True)
            raise MacControlError(
                "AppleScript执行异常",
                detail=str(e),
                context={'script': script[:100]}
            )
    
    def quit_app(self, app_name: str) -> bool:
        """
        关闭应用程序
        
        参数:
            app_name: 应用名称(如: "网易云音乐", "Safari")
        
        返回:
            bool: 是否成功关闭
        
        说明:
            使用AppleScript的quit命令优雅地关闭应用
        
        示例:
            success = mac_controller.quit_app("网易云音乐")
            if success:
                print("应用已关闭")
        """
        try:
            logger.info(f"正在关闭应用: {app_name}")
            
            script = f'quit app "{app_name}"'
            self._execute_applescript(script)
            
            logger.info(f"成功关闭应用: {app_name}")
            return True
            
        except MacControlError as e:
            logger.error(f"关闭应用失败: {e}")
            return False
    
    def open_app(self, app_name: str) -> bool:
        """
        打开应用程序
        
        参数:
            app_name: 应用名称(如: "Safari", "企业微信")
        
        返回:
            bool: 是否成功打开
        
        说明:
            使用AppleScript的activate命令打开应用
        
        示例:
            success = mac_controller.open_app("Safari")
            if success:
                print("应用已打开")
        """
        try:
            logger.info(f"正在打开应用: {app_name}")
            
            script = f'tell application "{app_name}" to activate'
            self._execute_applescript(script)
            
            logger.info(f"成功打开应用: {app_name}")
            return True
            
        except MacControlError as e:
            logger.error(f"打开应用失败: {e}")
            return False
    
    def is_app_running(self, app_name: str) -> bool:
        """
        检查应用是否正在运行
        
        参数:
            app_name: 应用名称
        
        返回:
            bool: 是否正在运行
        
        示例:
            if mac_controller.is_app_running("Safari"):
                print("Safari正在运行")
        """
        try:
            script = f'''
                tell application "System Events"
                    return (name of processes) contains "{app_name}"
                end tell
            '''
            
            result = self._execute_applescript(script)
            is_running = result.lower() == 'true'
            
            logger.debug(f"应用 {app_name} 运行状态: {is_running}")
            return is_running
            
        except MacControlError:
            return False
    
    def get_running_apps(self) -> List[str]:
        """
        获取所有正在运行的应用列表
        
        返回:
            List[str]: 应用名称列表
        
        示例:
            apps = mac_controller.get_running_apps()
            print(f"正在运行 {len(apps)} 个应用")
        """
        try:
            script = '''
                tell application "System Events"
                    return name of every process whose background only is false
                end tell
            '''
            
            result = self._execute_applescript(script)
            
            if result:
                apps = [app.strip() for app in result.split(', ')]
                logger.debug(f"获取到 {len(apps)} 个运行中的应用")
                return apps
            
            return []
            
        except MacControlError:
            logger.error("获取运行中的应用列表失败")
            return []
    
    def disable_notifications(self, bundle_id: str) -> bool:
        """
        禁用应用的通知权限
        
        参数:
            bundle_id: 应用的Bundle ID(如: "com.netease.163music")
        
        返回:
            bool: 是否成功禁用
        
        说明:
            需要"辅助功能"权限才能修改通知设置
            macOS 12+可能需要手动授权
        
        注意:
            此功能可能受到macOS安全限制,建议引导用户手动设置
        
        示例:
            success = mac_controller.disable_notifications("com.netease.163music")
            if not success:
                print("请手动在系统设置中禁用通知")
        """
        try:
            logger.info(f"正在禁用通知: {bundle_id}")
            logger.warning("通知权限修改需要用户手动操作,将打开系统设置")
            
            script = '''
                tell application "System Preferences"
                    activate
                    reveal pane id "com.apple.preference.notifications"
                end tell
            '''
            self._execute_applescript(script)
            
            logger.info("已打开通知设置面板,请手动禁用通知")
            return True
            
        except MacControlError as e:
            logger.error(f"打开通知设置失败: {e}")
            return False
    
    def get_macos_version(self) -> Optional[str]:
        """
        获取macOS版本
        
        返回:
            Optional[str]: macOS版本号(如: "13.0")
        
        示例:
            version = mac_controller.get_macos_version()
            print(f"macOS版本: {version}")
        """
        try:
            result = subprocess.run(
                ['sw_vers', '-productVersion'],
                capture_output=True,
                text=True,
                check=True
            )
            
            version = result.stdout.strip()
            logger.debug(f"macOS版本: {version}")
            return version
            
        except Exception as e:
            logger.error(f"获取macOS版本失败: {e}")
            return None
    
    def get_bundle_id(self, app_name: str) -> Optional[str]:
        """
        获取应用的Bundle ID
        
        参数:
            app_name: 应用名称
        
        返回:
            Optional[str]: Bundle ID(如: "com.apple.Safari")
        
        说明:
            通过osascript查询应用的Bundle ID
        
        示例:
            bundle_id = mac_controller.get_bundle_id("Safari")
            # "com.apple.Safari"
        """
        try:
            script = f'''
                tell application "System Events"
                    return bundle identifier of application process "{app_name}"
                end tell
            '''
            
            bundle_id = self._execute_applescript(script)
            logger.debug(f"应用 {app_name} 的Bundle ID: {bundle_id}")
            return bundle_id
            
        except MacControlError:
            logger.error(f"获取Bundle ID失败: {app_name}")
            return None
    
    def open_system_preferences(self, pane_id: Optional[str] = None) -> bool:
        """
        打开系统设置
        
        参数:
            pane_id: 设置面板ID(可选)
                - "com.apple.preference.security" - 安全性与隐私
                - "com.apple.preference.notifications" - 通知
                - "com.apple.preference.keyboard" - 键盘
        
        返回:
            bool: 是否成功打开
        
        示例:
            # 打开安全性与隐私设置
            mac_controller.open_system_preferences("com.apple.preference.security")
        """
        try:
            if pane_id:
                script = f'''
                    tell application "System Preferences"
                        activate
                        reveal pane id "{pane_id}"
                    end tell
                '''
            else:
                script = '''
                    tell application "System Preferences"
                        activate
                    end tell
                '''
            
            self._execute_applescript(script)
            logger.info(f"已打开系统设置: {pane_id or '主页'}")
            return True
            
        except MacControlError as e:
            logger.error(f"打开系统设置失败: {e}")
            return False
    
    def execute_shell_command(self, command: str) -> Optional[str]:
        """
        执行shell命令
        
        参数:
            command: shell命令
        
        返回:
            Optional[str]: 命令输出
        
        警告:
            此方法存在安全风险,仅用于可信命令
            不要执行用户提供的原始命令
        
        示例:
            output = mac_controller.execute_shell_command("ls -la ~")
        """
        try:
            logger.warning(f"执行shell命令: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Shell命令执行失败: {e.stderr}")
            raise MacControlError(
                "Shell命令执行失败",
                detail=e.stderr,
                context={'command': command}
            )
        except Exception as e:
            logger.error(f"Shell命令执行异常: {e}", exc_info=True)
            return None


mac_controller = MacController()
