"""
Mac系统控制模块 - Mac Controller

通过AppleScript控制macOS系统和应用程序。

主要功能:
1. 应用程序控制 - 打开、关闭、激活应用
2. 应用状态查询 - 查询应用是否运行
3. 系统信息获取 - macOS版本、Bundle ID等
4. 通知管理 - 引导用户管理应用通知权限
5. 系统设置 - 打开系统偏好设置面板

技术实现:
- 使用osascript执行AppleScript命令
- 使用subprocess模块调用系统命令
- 提供Python友好的API接口

安全考虑:
- 所有用户输入都经过转义,防止命令注入
- 不执行危险的系统操作
- 权限操作需要用户手动授权

使用示例:
    from infrastructure.mac_controller import MacController
    
    controller = MacController()
    
    # 打开应用
    controller.open_app("Safari")
    
    # 关闭应用
    controller.quit_app("Safari")
    
    # 检查应用是否运行
    is_running = controller.is_app_running("Safari")
    
    # 获取系统版本
    version = controller.get_macos_version()
"""

import subprocess
import platform
from typing import Optional, List
from infrastructure.logger import logger
from domain.exceptions import MacControlError


class MacController:
    """
    Mac系统控制器
    
    属性:
        is_macos: 标记是否运行在macOS系统
    
    设计说明:
        封装osascript和系统命令调用,提供统一的Python API。
        所有方法都会检查系统类型,非macOS系统会记录警告。
    """
    
    def __init__(self):
        """
        初始化Mac控制器
        
        检查系统类型,如果不是macOS会记录警告。
        """
        self.is_macos = platform.system() == 'Darwin'
        
        if not self.is_macos:
            logger.warning(
                f"当前系统不是macOS (系统: {platform.system()}), "
                f"Mac控制功能将不可用"
            )
        else:
            logger.debug("MacController初始化完成")
    
    def _check_macos(self):
        """
        检查是否运行在macOS系统
        
        抛出:
            MacControlError: 如果不是macOS系统
        """
        if not self.is_macos:
            raise MacControlError(
                "Mac控制功能仅在macOS系统可用",
                system=platform.system()
            )
    
    def _escape_applescript_string(self, text: str) -> str:
        """
        转义AppleScript字符串
        
        参数:
            text: 原始字符串
        
        返回:
            str: 转义后的字符串
        
        说明:
            防止AppleScript注入攻击
        """
        return text.replace('"', '\\"').replace('\\', '\\\\')
    
    def _execute_applescript(self, script: str, timeout: int = 10) -> str:
        """
        执行AppleScript脚本
        
        参数:
            script: AppleScript脚本内容
            timeout: 超时时间(秒)
        
        返回:
            str: 脚本执行输出
        
        抛出:
            MacControlError: 脚本执行失败
        
        示例:
            output = self._execute_applescript('tell application "Safari" to activate')
        """
        self._check_macos()
        
        try:
            logger.debug(f"执行AppleScript: {script[:100]}...")
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"AppleScript执行失败: {error_msg}")
            raise MacControlError(
                "AppleScript执行失败",
                script=script[:100],
                error=error_msg,
                cause=e
            )
        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript执行超时")
            raise MacControlError(
                "AppleScript执行超时",
                script=script[:100],
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"AppleScript执行错误: {e}", exc_info=True)
            raise MacControlError(
                "AppleScript执行错误",
                script=script[:100],
                cause=e
            )
    
    def open_app(self, app_name: str) -> bool:
        """
        打开应用程序
        
        参数:
            app_name: 应用名称(如"Safari", "网易云音乐")
        
        返回:
            bool: 打开是否成功
        
        说明:
            使用AppleScript的activate命令打开并激活应用。
            如果应用未安装会抛出异常。
        
        示例:
            controller.open_app("Safari")
            controller.open_app("网易云音乐")
        """
        app_name = self._escape_applescript_string(app_name)
        script = f'tell application "{app_name}" to activate'
        
        try:
            self._execute_applescript(script)
            logger.info(f"已打开应用: {app_name}")
            return True
        except MacControlError as e:
            logger.error(f"打开应用失败: {app_name}")
            raise
    
    def quit_app(self, app_name: str, force: bool = False) -> bool:
        """
        关闭应用程序
        
        参数:
            app_name: 应用名称
            force: 是否强制关闭(不保存)
        
        返回:
            bool: 关闭是否成功
        
        说明:
            - force=False: 正常退出,会提示保存
            - force=True: 强制退出,不保存未保存的内容
        
        示例:
            controller.quit_app("Safari")
            controller.quit_app("TextEdit", force=True)
        """
        app_name = self._escape_applescript_string(app_name)
        
        if force:
            script = f'tell application "{app_name}" to quit without saving'
        else:
            script = f'tell application "{app_name}" to quit'
        
        try:
            if not self.is_app_running(app_name):
                logger.info(f"应用未运行,无需关闭: {app_name}")
                return True
            
            self._execute_applescript(script)
            logger.info(f"已关闭应用: {app_name}")
            return True
        except MacControlError as e:
            logger.error(f"关闭应用失败: {app_name}")
            raise
    
    def is_app_running(self, app_name: str) -> bool:
        """
        检查应用是否正在运行
        
        参数:
            app_name: 应用名称
        
        返回:
            bool: 应用是否运行
        
        说明:
            查询System Events获取运行中的应用列表
        
        示例:
            if controller.is_app_running("Safari"):
                print("Safari正在运行")
        """
        app_name = self._escape_applescript_string(app_name)
        script = f'''
        tell application "System Events"
            set appList to name of every process
            return appList contains "{app_name}"
        end tell
        '''
        
        try:
            output = self._execute_applescript(script)
            is_running = output.lower() == 'true'
            logger.debug(f"应用运行状态 {app_name}: {is_running}")
            return is_running
        except MacControlError:
            logger.warning(f"无法查询应用状态: {app_name}")
            return False
    
    def get_running_apps(self) -> List[str]:
        """
        获取所有运行中的应用程序列表
        
        返回:
            List[str]: 运行中的应用名称列表
        
        示例:
            apps = controller.get_running_apps()
            for app in apps:
                print(f"运行中: {app}")
        """
        script = '''
        tell application "System Events"
            set appList to name of every process
            return appList
        end tell
        '''
        
        try:
            output = self._execute_applescript(script)
            apps = [app.strip() for app in output.split(',') if app.strip()]
            logger.debug(f"获取到{len(apps)}个运行中的应用")
            return apps
        except MacControlError:
            logger.error("获取运行中应用列表失败")
            return []
    
    def get_app_bundle_id(self, app_name: str) -> Optional[str]:
        """
        获取应用的Bundle ID
        
        参数:
            app_name: 应用名称
        
        返回:
            str: Bundle ID (如"com.apple.Safari"), 失败返回None
        
        说明:
            Bundle ID用于系统级别的应用标识
        
        示例:
            bundle_id = controller.get_app_bundle_id("Safari")
            # 返回: "com.apple.Safari"
        """
        app_name = self._escape_applescript_string(app_name)
        script = f'id of application "{app_name}"'
        
        try:
            output = self._execute_applescript(script)
            logger.debug(f"应用Bundle ID: {app_name} -> {output}")
            return output if output else None
        except MacControlError:
            logger.warning(f"无法获取Bundle ID: {app_name}")
            return None
    
    def get_macos_version(self) -> str:
        """
        获取macOS版本
        
        返回:
            str: macOS版本字符串(如"14.0")
        
        示例:
            version = controller.get_macos_version()
            print(f"macOS版本: {version}")
        """
        self._check_macos()
        
        try:
            version = platform.mac_ver()[0]
            logger.debug(f"macOS版本: {version}")
            return version
        except Exception as e:
            logger.error(f"获取macOS版本失败: {e}")
            return "unknown"
    
    def open_system_preferences(self, pane: Optional[str] = None) -> bool:
        """
        打开系统偏好设置
        
        参数:
            pane: 偏好设置面板ID(可选)
                - "com.apple.preference.security" - 安全性与隐私
                - "com.apple.preference.notifications" - 通知
                - "com.apple.preference.keyboard" - 键盘
                - None - 打开主界面
        
        返回:
            bool: 打开是否成功
        
        示例:
            # 打开系统偏好设置主界面
            controller.open_system_preferences()
            
            # 打开安全性与隐私
            controller.open_system_preferences("com.apple.preference.security")
        """
        if pane:
            pane = self._escape_applescript_string(pane)
            script = f'tell application "System Preferences" to reveal pane "{pane}"'
        else:
            script = 'tell application "System Preferences" to activate'
        
        try:
            self._execute_applescript(script)
            logger.info(f"已打开系统偏好设置: {pane or '主界面'}")
            return True
        except MacControlError:
            logger.error(f"打开系统偏好设置失败: {pane}")
            return False
    
    def guide_notification_settings(self, app_name: str) -> str:
        """
        引导用户设置应用通知权限
        
        参数:
            app_name: 应用名称
        
        返回:
            str: 引导说明文本
        
        说明:
            由于macOS安全限制,无法通过脚本直接修改通知权限,
            此方法提供引导说明,打开系统设置让用户手动操作。
        
        示例:
            guide = controller.guide_notification_settings("网易云音乐")
            print(guide)
        """
        guide_text = f"""
📢 设置 {app_name} 的通知权限

由于macOS安全限制,需要手动设置通知权限:

步骤:
1. 打开"系统偏好设置" → "通知"
2. 在左侧列表中找到"{app_name}"
3. 调整通知设置(允许/禁止通知)

提示: 您也可以点击下方链接直接打开通知设置面板
"""
        
        logger.info(f"引导用户设置通知权限: {app_name}")
        
        try:
            self.open_system_preferences("com.apple.preference.notifications")
        except Exception:
            pass
        
        return guide_text.strip()
    
    def guide_accessibility_permission(self) -> str:
        """
        引导用户授予辅助功能权限
        
        返回:
            str: 引导说明文本
        
        说明:
            某些Mac控制功能需要"辅助功能"权限。
            此方法提供引导说明。
        
        示例:
            guide = controller.guide_accessibility_permission()
            print(guide)
        """
        guide_text = """
🔐 授予辅助功能权限

某些系统控制功能需要"辅助功能"权限:

步骤:
1. 打开"系统偏好设置" → "安全性与隐私"
2. 点击"隐私"标签页
3. 在左侧列表选择"辅助功能"
4. 点击左下角锁图标,输入密码解锁
5. 勾选"终端"或您使用的终端应用
6. 重新运行程序

提示: 您也可以点击下方链接直接打开安全设置面板
"""
        
        logger.info("引导用户授予辅助功能权限")
        
        try:
            self.open_system_preferences("com.apple.preference.security")
        except Exception:
            pass
        
        return guide_text.strip()
    
    def __repr__(self) -> str:
        """返回控制器的字符串表示"""
        return f"MacController(macos={self.is_macos}, version={self.get_macos_version() if self.is_macos else 'N/A'})"
