"""
包管理器工厂 - Package Manager Factory

自动检测系统可用的包管理器并提供统一接口。
支持并发执行以提升性能。
"""

import platform
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from infrastructure.logger import logger
from infrastructure.package_manager_base import PackageManagerBase, PackageManagerType


class PackageManagerFactory:
    """
    包管理器工厂类
    
    功能:
    1. 自动检测系统可用的包管理器
    2. 提供统一的包管理接口
    3. 支持并发执行多个任务
    """
    
    _instance: Optional['PackageManagerFactory'] = None
    _manager: Optional[PackageManagerBase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._manager is None:
            self._manager = self._detect_package_manager()
    
    def _detect_package_manager(self) -> Optional[PackageManagerBase]:
        """
        自动检测系统可用的包管理器
        
        检测顺序:
        1. macOS: brew
        2. Debian/Ubuntu: apt
        3. RHEL/CentOS/Fedora: yum/dnf
        4. Arch: pacman
        5. Snap (通用)
        """
        system = platform.system().lower()
        logger.info(f"检测操作系统: {system}")
        
        from infrastructure.brew_executor import BrewExecutor
        from infrastructure.apt_executor import AptExecutor
        
        managers = [BrewExecutor(), AptExecutor()]
        
        for manager in managers:
            try:
                if manager.is_available():
                    logger.info(f"检测到可用的包管理器: {manager.get_name()}")
                    return manager
            except Exception as e:
                logger.debug(f"检查{manager.get_name()}失败: {e}")
                continue
        
        logger.warning("未检测到支持的包管理器")
        return BrewExecutor()
    
    def get_manager(self) -> PackageManagerBase:
        """获取当前系统的包管理器"""
        if self._manager is None:
            self._manager = self._detect_package_manager()
        return self._manager
    
    def search_concurrent(self, keywords: List[str], max_workers: int = 5) -> Dict[str, List[str]]:
        """
        并发搜索多个关键词
        
        参数:
            keywords: 搜索关键词列表
            max_workers: 最大并发数
        
        返回:
            Dict[str, List[str]]: {keyword: [package_names]}
        """
        manager = self.get_manager()
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_keyword = {
                executor.submit(manager.search, keyword): keyword 
                for keyword in keywords
            }
            
            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    results[keyword] = future.result()
                except Exception as e:
                    logger.error(f"并发搜索失败 ({keyword}): {e}")
                    results[keyword] = []
        
        return results
    
    def install_concurrent(
        self, 
        packages: List[str], 
        max_workers: int = 3,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        并发安装多个软件包
        
        参数:
            packages: 软件包名称列表
            max_workers: 最大并发数
            options: 安装选项
        
        返回:
            Dict[str, bool]: {package_name: success}
        """
        manager = self.get_manager()
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_package = {
                executor.submit(manager.install, package, options): package 
                for package in packages
            }
            
            for future in as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    results[package] = future.result()
                except Exception as e:
                    logger.error(f"并发安装失败 ({package}): {e}")
                    results[package] = False
        
        return results
    
    def get_info_concurrent(
        self, 
        packages: List[str], 
        max_workers: int = 5
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        并发获取多个软件包的详细信息
        
        参数:
            packages: 软件包名称列表
            max_workers: 最大并发数
        
        返回:
            Dict[str, Optional[Dict]]: {package_name: info}
        """
        manager = self.get_manager()
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_package = {
                executor.submit(manager.info, package): package 
                for package in packages
            }
            
            for future in as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    results[package] = future.result()
                except Exception as e:
                    logger.error(f"并发获取信息失败 ({package}): {e}")
                    results[package] = None
        
        return results


package_manager_factory = PackageManagerFactory()
