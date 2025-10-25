"""
命令行控制器 - CLI Controller

实现命令行界面，处理用户输入和输出展示。
"""

import sys
from typing import Optional, List

from service.package_service import PackageService
from domain.package import Package
from infrastructure.logger import logger


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
    
    # 卸载 drawio
    macmind uninstall drawio

更多信息:
    GitHub: https://github.com/RJ-SRE/aiAllControl
    文档: https://github.com/RJ-SRE/aiAllControl/blob/main/README.md
"""
        print(help_text)
