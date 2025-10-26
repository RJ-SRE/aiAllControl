"""
APT包管理器执行器 - APT Package Manager Executor

支持基于Debian/Ubuntu系统的apt包管理器。
"""

import subprocess
import json
import re
from typing import List, Dict, Any, Optional
from infrastructure.logger import logger
from infrastructure.package_manager_base import PackageManagerBase, PackageManagerType
from domain.exceptions import BrewError


class AptExecutor(PackageManagerBase):
    """APT包管理器执行器"""
    
    def __init__(self):
        self.apt_path = '/usr/bin/apt'
        self.apt_cache_path = '/usr/bin/apt-cache'
    
    def get_type(self) -> PackageManagerType:
        return PackageManagerType.APT
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.apt_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _execute(self, args: List[str], timeout: int = 30, use_sudo: bool = False) -> str:
        cmd = ['sudo'] if use_sudo else []
        cmd.extend([self.apt_path] + args)
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"命令执行失败: {e.stderr}"
            logger.error(error_msg)
            raise BrewError(
                "APT命令执行失败",
                detail=e.stderr,
                context={'command': ' '.join(args), 'exit_code': e.returncode}
            )
        except subprocess.TimeoutExpired as e:
            error_msg = f"命令执行超时: {' '.join(cmd)}"
            logger.error(error_msg)
            raise BrewError(
                "命令执行超时",
                detail=f"超时时间: {timeout}秒",
                context={'command': ' '.join(args), 'timeout': timeout}
            )
        except Exception as e:
            error_msg = f"命令执行异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BrewError(
                "APT命令执行异常",
                detail=str(e),
                context={'command': ' '.join(args)}
            )
    
    def search(self, keyword: str) -> List[str]:
        try:
            output = subprocess.run(
                [self.apt_cache_path, 'search', keyword],
                capture_output=True,
                text=True,
                timeout=30
            ).stdout
            
            packages = []
            for line in output.split('\n'):
                if line.strip():
                    match = re.match(r'^(\S+)\s+-', line)
                    if match:
                        packages.append(match.group(1))
            
            logger.info(f"搜索'{keyword}'找到{len(packages)}个结果")
            return packages
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def info(self, package: str) -> Dict[str, Any]:
        try:
            output = subprocess.run(
                [self.apt_cache_path, 'show', package],
                capture_output=True,
                text=True,
                timeout=10
            ).stdout
            
            info_dict = {}
            for line in output.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info_dict[key.strip().lower()] = value.strip()
            
            return {
                'name': info_dict.get('package', package),
                'desc': info_dict.get('description', ''),
                'version': info_dict.get('version', 'unknown'),
                'homepage': info_dict.get('homepage'),
            }
        except Exception as e:
            logger.error(f"获取包信息失败: {e}")
            raise BrewError(
                "软件包不存在",
                detail=f"在APT中未找到软件包: {package}",
                context={'package': package}
            )
    
    def install(self, package: str, options: Optional[Dict[str, Any]] = None) -> bool:
        try:
            logger.info(f"正在安装: {package}")
            self._execute(['install', '-y', package], timeout=300, use_sudo=True)
            logger.info(f"成功安装: {package}")
            return True
        except BrewError as e:
            logger.error(f"安装失败: {e}")
            return False
    
    def uninstall(self, package: str) -> bool:
        try:
            logger.info(f"正在卸载: {package}")
            self._execute(['remove', '-y', package], timeout=60, use_sudo=True)
            logger.info(f"成功卸载: {package}")
            return True
        except BrewError as e:
            logger.error(f"卸载失败: {e}")
            return False
    
    def list_installed(self) -> List[str]:
        try:
            output = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True,
                text=True,
                timeout=30
            ).stdout
            
            packages = []
            for line in output.split('\n'):
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append(parts[1])
            
            logger.debug(f"已安装{len(packages)}个包")
            return packages
        except Exception as e:
            logger.error(f"获取已安装包列表失败: {e}")
            return []
