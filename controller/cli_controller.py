"""
命令行控制器 - CLI Controller

实现命令行界面，处理用户输入和输出展示。
"""

import sys
from typing import Optional, List

from service.package_service import PackageService
from domain.package import Package
from infrastructure.logger import logger
from infrastructure.conversation import conversation_manager
from infrastructure.mac_controller import MacController
from infrastructure.ai_client import create_ai_client


class CLIController:
    """
    命令行控制器
    
    职责:
        1. 解析命令行参数
        2. 调用Service层处理业务逻辑
        3. 格式化并展示结果
        4. 处理用户交互（确认提示等）
    
    支持的命令:
        - search <query>: 搜索软件包
        - install <package>: 安装软件包
        - uninstall <package>: 卸载软件包
        - list: 列出已安装的软件包
        - info <package>: 显示软件包详细信息
        - chat: 进入交互式对话模式
        - mac <action> [args]: Mac系统控制
        - clear-cache: 清空缓存
        - help: 显示帮助信息
    
    设计模式: MVC中的Controller
        - 薄控制器：不包含业务逻辑
        - 只负责用户界面和Service调用
    """
    
    def __init__(self):
        """
        初始化CLI控制器
        
        依赖注入:
            - PackageService: 业务逻辑层服务
        """
        self.service = PackageService()
        self.mac_controller = MacController()
        logger.debug("CLIController初始化完成")
    
    def run(self, args: Optional[List[str]] = None):
        """
        运行CLI控制器
        
        参数:
            args: 命令行参数列表，默认使用sys.argv[1:]
        
        流程:
            1. 解析命令和参数
            2. 调用对应的命令处理方法
            3. 处理异常和错误
        
        示例:
            controller = CLIController()
            controller.run(['search', '绘图软件'])
        """
        if args is None:
            args = sys.argv[1:]
        
        if not args:
            self._show_help()
            return
        
        command = args[0].lower()
        params = args[1:]
        
        try:
            if command == 'search':
                self._handle_search(params)
            elif command == 'install':
                self._handle_install(params)
            elif command == 'uninstall':
                self._handle_uninstall(params)
            elif command == 'list':
                self._handle_list(params)
            elif command == 'info':
                self._handle_info(params)
            elif command == 'chat':
                self._handle_chat(params)
            elif command == 'mac':
                self._handle_mac(params)
            elif command == 'notification':
                self._handle_notification(params)
            elif command == 'shortcut':
                self._handle_shortcut(params)
            elif command == 'clear-cache':
                self._handle_clear_cache(params)
            elif command == 'help' or command == '--help' or command == '-h':
                self._show_help()
            else:
                print(f"❌ 未知命令: {command}")
                print("使用 'help' 查看帮助信息")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  操作已取消")
            sys.exit(0)
        except Exception as e:
            logger.error(f"执行命令时发生错误: {e}", exc_info=True)
            print(f"\n❌ 错误: {e}")
            sys.exit(1)
    
    def _handle_search(self, params: List[str]):
        """
        处理搜索命令
        
        参数:
            params: 搜索关键词列表
        
        命令格式:
            search <query>
        
        示例:
            search 绘图软件
            search "video editor"
        
        输出:
            - 搜索关键词和意图
            - 软件包列表（名称、描述、许可证、是否已安装）
        """
        if not params:
            print("❌ 请提供搜索关键词")
            print("用法: search <query>")
            return
        
        query = ' '.join(params)
        
        print(f"🔍 搜索: {query}")
        print()
        
        result = self.service.search_packages(query)
        
        if not result.packages:
            print(f"未找到匹配的软件包")
            return
        
        print(f"📊 找到 {result.total_count} 个结果")
        print(f"🎯 关键词: {result.keyword}")
        print(f"💡 意图: {result.intent}")
        print()
        
        for i, pkg in enumerate(result.packages, 1):
            self._print_package_summary(pkg, index=i)
        
        print()
        print(f"💡 提示: 使用 'info <package>' 查看详细信息")
        print(f"💡 提示: 使用 'install <package>' 安装软件包")
    
    def _handle_install(self, params: List[str]):
        """
        处理安装命令
        
        参数:
            params: 软件包名称
        
        命令格式:
            install <package> [--force]
        
        示例:
            install drawio
            install vim --force
        
        流程:
            1. 验证参数
            2. 获取包信息并展示
            3. 用户确认
            4. 调用Service安装
            5. 显示结果
        """
        if not params:
            print("❌ 请提供软件包名称")
            print("用法: install <package> [--force]")
            return
        
        package_name = params[0]
        force = '--force' in params or '-f' in params
        
        print(f"📦 准备安装: {package_name}")
        print()
        
        package = self.service.get_package_details(package_name)
        if not package:
            print(f"❌ 软件包不存在: {package_name}")
            return
        
        self._print_package_details(package)
        print()
        
        if package.is_installed and not force:
            print(f"✅ 软件包已安装")
            print(f"💡 提示: 使用 '--force' 参数强制重新安装")
            return
        
        if not self._confirm(f"确认安装 {package_name}?"):
            print("❌ 已取消安装")
            return
        
        print()
        print(f"⏳ 正在安装 {package_name}...")
        
        success = self.service.install_package(package_name, force=force)
        
        if success:
            print(f"✅ 安装成功!")
        else:
            print(f"❌ 安装失败")
            sys.exit(1)
    
    def _handle_uninstall(self, params: List[str]):
        """
        处理卸载命令
        
        参数:
            params: 软件包名称
        
        命令格式:
            uninstall <package>
        
        示例:
            uninstall drawio
        
        流程:
            1. 验证参数
            2. 检查是否已安装
            3. 用户确认
            4. 调用Service卸载
            5. 显示结果
        """
        if not params:
            print("❌ 请提供软件包名称")
            print("用法: uninstall <package>")
            return
        
        package_name = params[0]
        
        print(f"📦 准备卸载: {package_name}")
        print()
        
        package = self.service.get_package_details(package_name)
        if not package:
            print(f"❌ 软件包不存在: {package_name}")
            return
        
        if not package.is_installed:
            print(f"ℹ️  软件包未安装: {package_name}")
            return
        
        if not self._confirm(f"确认卸载 {package_name}?"):
            print("❌ 已取消卸载")
            return
        
        print()
        print(f"⏳ 正在卸载 {package_name}...")
        
        success = self.service.uninstall_package(package_name)
        
        if success:
            print(f"✅ 卸载成功!")
        else:
            print(f"❌ 卸载失败")
            sys.exit(1)
    
    def _handle_list(self, params: List[str]):
        """
        处理列表命令
        
        参数:
            params: 可选参数（暂未使用）
        
        命令格式:
            list
        
        示例:
            list
        
        输出:
            已安装的软件包列表
        """
        print("📋 已安装的软件包:")
        print()
        
        packages = self.service.list_installed_packages()
        
        if not packages:
            print("未安装任何软件包")
            return
        
        print(f"共 {len(packages)} 个软件包\n")
        
        for i, pkg in enumerate(packages, 1):
            self._print_package_summary(pkg, index=i)
        
        print()
        print(f"💡 提示: 使用 'info <package>' 查看详细信息")
    
    def _handle_info(self, params: List[str]):
        """
        处理详情命令
        
        参数:
            params: 软件包名称
        
        命令格式:
            info <package>
        
        示例:
            info drawio
        
        输出:
            软件包的详细信息
        """
        if not params:
            print("❌ 请提供软件包名称")
            print("用法: info <package>")
            return
        
        package_name = params[0]
        
        package = self.service.get_package_details(package_name)
        if not package:
            print(f"❌ 软件包不存在: {package_name}")
            return
        
        self._print_package_details(package)
    
    def _handle_clear_cache(self, params: List[str]):
        """
        处理清空缓存命令
        
        参数:
            params: 可选参数（暂未使用）
        
        命令格式:
            clear-cache
        
        示例:
            clear-cache
        """
        if not self._confirm("确认清空所有缓存?"):
            print("❌ 已取消")
            return
        
        self.service.clear_cache()
        print("✅ 缓存已清空")
    
    def _handle_chat(self, params: List[str]):
        """
        处理交互式对话命令
        
        参数:
            params: 可选参数（暂未使用）
        
        命令格式:
            chat
        
        功能:
            进入交互式AI对话模式，支持持续对话和上下文记忆
        
        示例:
            chat
        """
        print("💬 进入交互式对话模式")
        print("提示: 输入 'exit' 或 'quit' 退出对话")
        print("提示: 输入 'clear' 清空对话历史")
        print("提示: 输入 'save' 保存当前会话")
        print("=" * 60)
        print()
        
        try:
            ai_client = create_ai_client()
        except Exception as e:
            print(f"❌ AI客户端初始化失败: {e}")
            print("请检查API密钥配置")
            return
        
        conversation_manager.add_system_message(
            conversation_manager.get_optimized_system_prompt()
        )
        
        while True:
            try:
                user_input = input("😊 你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 再见！")
                    break
                
                if user_input.lower() == 'clear':
                    conversation_manager.clear_history()
                    print("✅ 对话历史已清空\n")
                    continue
                
                if user_input.lower() == 'save':
                    conversation_manager.save_session()
                    print("✅ 会话已保存\n")
                    continue
                
                conversation_manager.add_user_message(user_input)
                
                print("🤖 AI: ", end="", flush=True)
                
                context = conversation_manager.get_context()
                
                try:
                    response_text = "抱歉，我暂时无法理解这个请求。请尝试询问软件搜索、安装等相关问题。"
                    
                    import json
                    response = ai_client.client.chat.completions.create(
                        model=ai_client.model,
                        messages=context
                    )
                    
                    response_text = response.choices[0].message.content
                    
                except Exception as e:
                    logger.error(f"AI响应失败: {e}", exc_info=True)
                    response_text = f"抱歉，AI服务暂时不可用: {str(e)}"
                
                print(response_text)
                print()
                
                conversation_manager.add_assistant_message(response_text)
                
            except KeyboardInterrupt:
                print("\n\n👋 对话已中断")
                break
            except Exception as e:
                logger.error(f"对话处理错误: {e}", exc_info=True)
                print(f"\n❌ 错误: {e}\n")
    
    def _handle_mac(self, params: List[str]):
        """
        处理Mac系统控制命令
        
        参数:
            params: 子命令和参数
        
        命令格式:
            mac open <app>        打开应用
            mac quit <app>        关闭应用
            mac status <app>      查询应用状态
            mac apps              列出运行中的应用
            mac version           显示macOS版本
            mac notify <title> <message>  发送系统通知
        
        示例:
            mac open Safari
            mac quit "网易云音乐"
            mac status Safari
        """
        if not params:
            print("❌ 请提供Mac控制子命令")
            print("用法: mac <action> [args]")
            print("可用操作: open, quit, status, apps, version")
            return
        
        action = params[0].lower()
        args = params[1:]
        
        try:
            if action == 'open':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: mac open <app>")
                    return
                app_name = ' '.join(args)
                self.mac_controller.open_app(app_name)
                print(f"✅ 已打开应用: {app_name}")
            
            elif action == 'quit':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: mac quit <app>")
                    return
                app_name = ' '.join(args)
                self.mac_controller.quit_app(app_name)
                print(f"✅ 已关闭应用: {app_name}")
            
            elif action == 'status':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: mac status <app>")
                    return
                app_name = ' '.join(args)
                is_running = self.mac_controller.is_app_running(app_name)
                status = "运行中 ✓" if is_running else "未运行 ✗"
                print(f"应用状态: {app_name} - {status}")
            
            elif action == 'apps':
                apps = self.mac_controller.get_running_apps()
                print(f"📱 运行中的应用 (共{len(apps)}个):")
                print()
                for i, app in enumerate(apps, 1):
                    print(f"{i}. {app}")
            
            elif action == 'version':
                version = self.mac_controller.get_macos_version()
                print(f"🍎 macOS版本: {version}")
            
            elif action == 'notify':
                if len(args) < 2:
                    print("❌ 请提供通知标题和内容")
                    print("用法: mac notify <title> <message> [subtitle]")
                    return
                title = args[0]
                message = args[1]
                subtitle = args[2] if len(args) > 2 else None
                self.mac_controller.send_notification(title, message, subtitle)
                print(f"✅ 已发送通知")
            
            else:
                print(f"❌ 未知操作: {action}")
                print("可用操作: open, quit, status, apps, version, notify")
        
        except Exception as e:
            logger.error(f"Mac控制操作失败: {e}", exc_info=True)
            print(f"❌ 操作失败: {e}")
    
    def _print_package_summary(self, package: Package, index: Optional[int] = None):
        """
        打印软件包摘要信息
        
        参数:
            package: Package对象
            index: 序号（可选）
        
        输出格式:
            1. package-name (version) [已安装]
               描述信息
               许可证: MIT | 类型: formula
        """
        prefix = f"{index}. " if index else "- "
        installed_mark = " ✓" if package.is_installed else ""
        
        print(f"{prefix}{package.name} ({package.version}){installed_mark}")
        
        if package.description:
            desc = package.description
            if len(desc) > 80:
                desc = desc[:77] + "..."
            print(f"   {desc}")
        
        print(f"   许可证: {package.license.value} | 类型: {package.package_type.value}")
        print()
    
    def _print_package_details(self, package: Package):
        """
        打印软件包详细信息
        
        参数:
            package: Package对象
        
        输出格式:
            详细的软件包信息，包括所有字段
        """
        print("=" * 60)
        print(f"📦 软件包: {package.name}")
        print("=" * 60)
        print()
        
        print(f"📝 描述: {package.description or '无'}")
        print(f"🔢 版本: {package.version}")
        print(f"📋 许可证: {package.license.value}")
        print(f"📦 类型: {package.package_type.value}")
        
        if package.homepage:
            print(f"🔗 主页: {package.homepage}")
        
        if package.downloads > 0:
            print(f"📥 下载量: {package.downloads:,}")
        
        if package.last_updated:
            print(f"🕐 更新时间: {package.last_updated}")
        
        print(f"✅ 已安装: {'是' if package.is_installed else '否'}")
        
        print()
        print("=" * 60)
    
    def _confirm(self, message: str) -> bool:
        """
        用户确认提示
        
        参数:
            message: 确认消息
        
        返回:
            bool: True表示确认，False表示取消
        
        交互:
            显示消息并等待用户输入 y/n
        """
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("请输入 y 或 n")
    
    def _handle_notification(self, params: List[str]):
        """
        处理通知管理命令
        
        参数:
            params: 子命令和参数
        
        命令格式:
            notification enable <app>     启用应用通知
            notification disable <app>    禁用应用通知
            notification info <app>       查看通知设置
            notification send <title> <message> [副标题]  发送通知
        """
        if not params:
            print("❌ 请提供通知管理子命令")
            print("用法: notification <action> [args]")
            print("可用操作: enable, disable, info, send")
            return
        
        action = params[0].lower()
        args = params[1:]
        
        try:
            if action == 'enable':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: notification enable <app>")
                    return
                app_name = ' '.join(args)
                guide = self.mac_controller.enable_app_notifications(app_name)
                print(guide)
            
            elif action == 'disable':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: notification disable <app>")
                    return
                app_name = ' '.join(args)
                guide = self.mac_controller.disable_app_notifications(app_name)
                print(guide)
            
            elif action == 'info':
                if not args:
                    print("❌ 请提供应用名称")
                    print("用法: notification info <app>")
                    return
                app_name = ' '.join(args)
                settings = self.mac_controller.get_notification_settings(app_name)
                if settings:
                    print(f"🔔 {settings['app_name']} 通知设置")
                    print(f"Bundle ID: {settings['bundle_id']}")
                    print(f"设置路径: {settings['settings_path']}")
                    print(f"注意: {settings['note']}")
                else:
                    print(f"❌ 无法获取通知设置: {app_name}")
            
            elif action == 'send':
                if len(args) < 2:
                    print("❌ 请提供通知标题和内容")
                    print("用法: notification send <title> <message> [subtitle]")
                    return
                title = args[0]
                message = args[1]
                subtitle = args[2] if len(args) > 2 else None
                success = self.mac_controller.send_notification(title, message, subtitle)
                if success:
                    print("✅ 通知已发送")
                else:
                    print("❌ 通知发送失败")
            
            else:
                print(f"❌ 未知操作: {action}")
                print("可用操作: enable, disable, info, send")
        
        except Exception as e:
            logger.error(f"通知管理操作失败: {e}", exc_info=True)
            print(f"❌ 操作失败: {e}")
    
    def _handle_shortcut(self, params: List[str]):
        """
        处理快捷键管理命令
        
        参数:
            params: 子命令和参数
        
        命令格式:
            shortcut create <快捷键> <操作> [app1] [app2] ...  创建快捷键
            shortcut check <快捷键>                        检查冲突
            shortcut install-tool                         安装Hammerspoon
        """
        if not params:
            print("❌ 请提供快捷键管理子命令")
            print("用法: shortcut <action> [args]")
            print("可用操作: create, check, install-tool")
            return
        
        action = params[0].lower()
        args = params[1:]
        
        try:
            if action == 'create':
                if len(args) < 2:
                    print("❌ 请提供快捷键和操作描述")
                    print("用法: shortcut create <快捷键> <操作> [app1] [app2] ...")
                    print("示例: shortcut create 'Command+Shift+L' '打开工作应用' '企业微信' 'WPS'")
                    return
                
                shortcut = args[0]
                action_desc = args[1]
                apps = args[2:] if len(args) > 2 else None
                
                guide = self.mac_controller.create_keyboard_shortcut_guide(
                    shortcut, action_desc, apps
                )
                print(guide)
            
            elif action == 'check':
                if not args:
                    print("❌ 请提供要检查的快捷键")
                    print("用法: shortcut check <快捷键>")
                    print("示例: shortcut check 'Command+L'")
                    return
                
                shortcut = args[0]
                result = self.mac_controller.check_keyboard_shortcut_conflicts(shortcut)
                
                if result['has_conflict']:
                    print(f"⚠️  快捷键冲突检测")
                    print(f"快捷键: {result['shortcut']}")
                    print(f"冲突项: {result['conflicts_with']}")
                    print(f"💡 {result['suggestion']}")
                else:
                    print(f"✅ 未发现冲突")
                    print(f"快捷键: {result['shortcut']}")
                    print(f"注意: {result['note']}")
            
            elif action == 'install-tool':
                print("🔧 准备安装 Hammerspoon...")
                print("")
                success = self.mac_controller.install_hammerspoon()
                if not success:
                    print("\n或者手动安装:")
                    print("brew install hammerspoon --cask")
            
            else:
                print(f"❌ 未知操作: {action}")
                print("可用操作: create, check, install-tool")
        
        except Exception as e:
            logger.error(f"快捷键管理操作失败: {e}", exc_info=True)
            print(f"❌ 操作失败: {e}")
    
    def _show_help(self):
        """
        显示帮助信息
        
        输出:
            命令列表和使用说明
        """
        help_text = """
🧠 MacMind - AI 驱动的软件管理工具

用法:
    macmind <command> [arguments]

命令:
    search <query>        搜索软件包
                          示例: macmind search 绘图软件
    
    install <package>     安装软件包
                          示例: macmind install drawio
                          选项: --force 强制重新安装
    
    uninstall <package>   卸载软件包
                          示例: macmind uninstall drawio
    
    list                  列出已安装的软件包
                          示例: macmind list
    
    info <package>        显示软件包详细信息
                          示例: macmind info vim
    
    chat                  进入交互式AI对话模式
                          示例: macmind chat
                          功能: 持续对话、上下文记忆、会话保存
    
    mac <action> [args]   Mac系统控制
                          示例: macmind mac open Safari
                          操作: open, quit, status, apps, version, notify
    
    notification <action> 通知管理
                          示例: macmind notification disable Safari
                          操作: enable, disable, info, send
    
    shortcut <action>     快捷键管理
                          示例: macmind shortcut create 'Command+L' '打开应用'
                          操作: create, check, install-tool
    
    clear-cache           清空所有缓存
                          示例: macmind clear-cache
    
    help                  显示此帮助信息
                          示例: macmind help

示例:
    # 搜索绘图软件
    macmind search 绘图软件
    
    # 安装 drawio
    macmind install drawio
    
    # 列出已安装的软件
    macmind list
    
    # 查看 vim 的详细信息
    macmind info vim
    
    # 进入AI对话模式
    macmind chat
    
    # 打开Safari浏览器
    macmind mac open Safari
    
    # 查询应用运行状态
    macmind mac status Safari
    
    # 禁用应用通知
    macmind notification disable Safari
    
    # 创建快捷键
    macmind shortcut create 'Command+Shift+L' '打开工作应用' '企业微信' 'WPS'
    
    # 卸载 drawio
    macmind uninstall drawio

更多信息:
    GitHub: https://github.com/RJ-SRE/aiAllControl
    文档: https://github.com/RJ-SRE/aiAllControl/blob/main/README.md
"""
        print(help_text)
