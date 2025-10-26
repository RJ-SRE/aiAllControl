"""
工具执行器模块 - Tool Executor

执行AI通过Function Calling请求的工具调用。

设计模式:
1. 命令模式 - 将工具调用封装为可执行命令
2. 策略模式 - 不同工具有不同的执行策略

主要功能:
1. 工具调用分发 - 根据工具名称分发到对应处理函数
2. 参数验证 - 确保参数完整性和类型正确
3. 错误处理 - 捕获并格式化错误信息
4. 结果格式化 - 统一返回格式

使用示例:
    from infrastructure.tool_executor import ToolExecutor
    
    executor = ToolExecutor()
    
    result = executor.execute("search_software", {
        "query": "绘图软件",
        "max_results": 5
    })
    
    if result["success"]:
        print(result["data"])
    else:
        print(result["error"])
"""

import json
from typing import Dict, Any, List
from infrastructure.logger import logger
from infrastructure.mac_controller import MacController
from service.package_service import PackageService
from domain.exceptions import MacControlError


class ToolExecutor:
    """
    工具执行器
    
    属性:
        package_service: 软件包管理服务
        mac_controller: Mac系统控制器
    
    设计说明:
        作为工具调用的中央分发器,负责:
        1. 验证工具名称和参数
        2. 调用对应的服务方法
        3. 统一错误处理和结果格式化
    """
    
    def __init__(self):
        """
        初始化工具执行器
        
        说明:
            初始化所需的服务和控制器
        """
        self.package_service = PackageService()
        self.mac_controller = MacController()
        logger.debug("ToolExecutor初始化完成")
    
    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用
        
        参数:
            function_name: 工具函数名称
            arguments: 工具参数字典
        
        返回:
            Dict[str, Any]: 执行结果
                - success: bool - 是否成功
                - data: Any - 成功时的数据
                - error: str - 失败时的错误信息
        
        工作流程:
            1. 记录工具调用
            2. 根据函数名分发到对应处理方法
            3. 捕获异常并格式化错误
            4. 返回统一格式的结果
        
        示例:
            >>> executor = ToolExecutor()
            >>> result = executor.execute("search_software", {"query": "vim"})
            >>> result["success"]
            True
        """
        logger.info(f"执行工具调用: {function_name}, 参数: {arguments}")
        
        try:
            if function_name == "search_software":
                return self._search_software(arguments)
            elif function_name == "install_software":
                return self._install_software(arguments)
            elif function_name == "list_installed_software":
                return self._list_installed_software(arguments)
            elif function_name == "open_app":
                return self._open_app(arguments)
            elif function_name == "quit_app":
                return self._quit_app(arguments)
            elif function_name == "check_app_status":
                return self._check_app_status(arguments)
            elif function_name == "get_system_info":
                return self._get_system_info(arguments)
            else:
                return {
                    "success": False,
                    "error": f"未知的工具: {function_name}"
                }
        
        except Exception as e:
            logger.error(f"工具执行失败: {function_name}, 错误: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
    
    def _search_software(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索软件包
        
        参数:
            arguments: {"query": str, "max_results": int (可选)}
        
        返回:
            Dict: 搜索结果
        """
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        
        if not query:
            return {
                "success": False,
                "error": "搜索关键词不能为空"
            }
        
        result = self.package_service.search_packages(query, max_results=max_results)
        
        packages_data = [
            {
                "name": pkg.name,
                "description": pkg.description,
                "license": pkg.license,
                "homepage": pkg.homepage
            }
            for pkg in result.packages
        ]
        
        return {
            "success": True,
            "data": {
                "keyword": result.keyword,
                "intent": result.intent,
                "total_count": result.total_count,
                "packages": packages_data
            }
        }
    
    def _install_software(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        安装软件包
        
        参数:
            arguments: {"package_name": str}
        
        返回:
            Dict: 安装结果
        
        说明:
            这是敏感操作,在实际执行前应该有用户确认机制
        """
        package_name = arguments.get("package_name", "")
        
        if not package_name:
            return {
                "success": False,
                "error": "软件包名称不能为空"
            }
        
        success = self.package_service.install_package(package_name)
        
        if success:
            return {
                "success": True,
                "data": {
                    "package_name": package_name,
                    "message": f"成功安装 {package_name}"
                }
            }
        else:
            return {
                "success": False,
                "error": f"安装 {package_name} 失败"
            }
    
    def _list_installed_software(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出已安装的软件
        
        参数:
            arguments: {} (无参数)
        
        返回:
            Dict: 已安装软件列表
        """
        packages = self.package_service.list_installed_packages()
        
        packages_data = [
            {
                "name": pkg.name,
                "version": pkg.version,
                "description": pkg.description
            }
            for pkg in packages
        ]
        
        return {
            "success": True,
            "data": {
                "count": len(packages_data),
                "packages": packages_data
            }
        }
    
    def _open_app(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        打开应用程序
        
        参数:
            arguments: {"app_name": str}
        
        返回:
            Dict: 执行结果
        """
        app_name = arguments.get("app_name", "")
        
        if not app_name:
            return {
                "success": False,
                "error": "应用名称不能为空"
            }
        
        try:
            self.mac_controller.open_app(app_name)
            return {
                "success": True,
                "data": {
                    "app_name": app_name,
                    "message": f"已打开 {app_name}"
                }
            }
        except MacControlError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _quit_app(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        关闭应用程序
        
        参数:
            arguments: {"app_name": str}
        
        返回:
            Dict: 执行结果
        """
        app_name = arguments.get("app_name", "")
        
        if not app_name:
            return {
                "success": False,
                "error": "应用名称不能为空"
            }
        
        try:
            self.mac_controller.quit_app(app_name)
            return {
                "success": True,
                "data": {
                    "app_name": app_name,
                    "message": f"已关闭 {app_name}"
                }
            }
        except MacControlError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_app_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查应用状态
        
        参数:
            arguments: {"app_name": str}
        
        返回:
            Dict: 应用状态
        """
        app_name = arguments.get("app_name", "")
        
        if not app_name:
            return {
                "success": False,
                "error": "应用名称不能为空"
            }
        
        try:
            is_running = self.mac_controller.is_app_running(app_name)
            return {
                "success": True,
                "data": {
                    "app_name": app_name,
                    "is_running": is_running,
                    "status": "运行中" if is_running else "未运行"
                }
            }
        except MacControlError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_system_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取系统信息
        
        参数:
            arguments: {} (无参数)
        
        返回:
            Dict: 系统信息
        """
        try:
            version = self.mac_controller.get_macos_version()
            return {
                "success": True,
                "data": {
                    "macos_version": version,
                    "system": "macOS"
                }
            }
        except MacControlError as e:
            return {
                "success": False,
                "error": str(e)
            }
