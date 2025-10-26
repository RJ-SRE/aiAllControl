"""
包管理器基类 - Package Manager Base

定义所有包管理器的统一接口,支持多种包管理系统。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum


class PackageManagerType(Enum):
    BREW = "brew"
    APT = "apt"
    YUM = "yum"
    DNF = "dnf"
    SNAP = "snap"
    PACMAN = "pacman"


class PackageManagerBase(ABC):
    """
    包管理器抽象基类
    
    所有包管理器必须实现以下方法:
    - search: 搜索软件包
    - info: 获取包详细信息
    - install: 安装软件包
    - uninstall: 卸载软件包
    - list_installed: 列出已安装的包
    - is_available: 检查包管理器是否可用
    """
    
    @abstractmethod
    def get_type(self) -> PackageManagerType:
        """返回包管理器类型"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查包管理器是否可用"""
        pass
    
    @abstractmethod
    def search(self, keyword: str) -> List[str]:
        """搜索软件包"""
        pass
    
    @abstractmethod
    def info(self, package: str) -> Dict[str, Any]:
        """获取软件包详细信息"""
        pass
    
    @abstractmethod
    def install(self, package: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """安装软件包"""
        pass
    
    @abstractmethod
    def uninstall(self, package: str) -> bool:
        """卸载软件包"""
        pass
    
    @abstractmethod
    def list_installed(self) -> List[str]:
        """列出已安装的软件包"""
        pass
    
    def get_name(self) -> str:
        """返回包管理器名称"""
        return self.get_type().value
