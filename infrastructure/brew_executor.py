"""
Homebrew命令执行器 - Homebrew Command Executor

封装所有与Homebrew交互的底层操作，提供类型安全的接口。

设计原则: 单一职责原则 (Single Responsibility Principle)
- 只负责执行Homebrew命令
- 不包含业务逻辑
- 不处理数据转换（由Repository层负责）

主要功能:
1. 搜索软件包 (search)
2. 获取包详细信息 (info)
3. 安装软件包 (install)
4. 列出已安装的包 (list_installed)

错误处理:
- 命令执行失败抛出RuntimeError
- 超时控制避免长时间等待
- 详细的错误日志记录

使用示例:
    from infrastructure.brew_executor import brew
    
    # 搜索软件
    packages = brew.search('drawing')
    
    # 获取详细信息
    info = brew.info('drawio')
    
    # 安装软件
    success = brew.install('drawio', is_cask=True)
"""

import subprocess
import json
from typing import List, Dict, Any
from infrastructure.logger import logger
from infrastructure.config import config


class BrewExecutor:
    """
    Homebrew命令执行器
    
    属性:
        brew_path: Homebrew可执行文件的完整路径
    
    设计说明:
        封装subprocess调用，统一处理命令执行、
        错误处理、超时控制和日志记录。
    """
    
    def __init__(self):
        """
        初始化执行器
        
        从配置中读取Homebrew路径，默认为Apple Silicon Mac的路径。
        Intel Mac的路径通常是 /usr/local/bin/brew
        """
        self.brew_path = config.get('homebrew_path', '/opt/homebrew/bin/brew')
    
    def _execute(self, args: List[str], timeout: int = 30) -> str:
        """
        执行brew命令的核心方法
        
        参数:
            args: 命令参数列表，例如 ['search', 'drawing']
            timeout: 命令超时时间（秒），默认30秒
        
        返回:
            str: 命令的标准输出
        
        抛出:
            RuntimeError: 命令执行失败或超时
        
        工作流程:
        1. 构建完整命令
        2. 记录调试日志
        3. 执行命令（捕获输出）
        4. 处理错误和超时
        
        示例:
            output = self._execute(['search', 'vim'])
            # 等同于在终端执行: /opt/homebrew/bin/brew search vim
        """
        # 步骤1: 构建完整命令
        # ['/opt/homebrew/bin/brew', 'search', 'vim']
        cmd = [self.brew_path] + args
        
        # 步骤2: 记录命令到日志（便于调试）
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 步骤3: 执行命令
            # capture_output=True: 捕获stdout和stderr
            # text=True: 输出为字符串而不是bytes
            # timeout: 超时控制
            # check=True: 非零退出码抛出异常
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            # 步骤4a: 处理命令执行失败
            # CalledProcessError: 命令返回非零退出码
            error_msg = f"命令执行失败: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(f"Homebrew命令失败: {e.stderr}")
            
        except subprocess.TimeoutExpired:
            # 步骤4b: 处理超时
            error_msg = f"命令执行超时: {' '.join(cmd)}"
            logger.error(error_msg)
            raise RuntimeError("命令执行超时")
    
    def search(self, keyword: str) -> List[str]:
        """
        搜索软件包
        
        参数:
            keyword: 搜索关键词
        
        返回:
            List[str]: 匹配的包名列表
        
        说明:
            执行 brew search <keyword> 命令，
            解析输出为包名列表。
        
        输出格式:
            Homebrew返回的是多行文本，每行一个包名:
            drawio
            drawing
            draw-things
            
        示例:
            packages = brew.search('drawing')
            # 返回: ['drawio', 'drawing', 'draw-things']
        """
        # 执行搜索命令
        output = self._execute(['search', keyword])
        
        # 解析输出：分割行，去除空行和空格
        packages = [
            line.strip() 
            for line in output.split('\n') 
            if line.strip()  # 过滤空行
        ]
        
        # 记录搜索结果
        logger.info(f"搜索'{keyword}'找到{len(packages)}个结果")
        
        return packages
    
    def info(self, package: str) -> Dict[str, Any]:
        """
        获取软件包的详细信息
        
        参数:
            package: 包名
        
        返回:
            Dict[str, Any]: 包的详细信息字典
        
        抛出:
            RuntimeError: 包不存在
        
        说明:
            执行 brew info --json=v2 <package> 命令，
            返回JSON格式的包信息。
        
        返回数据结构:
            {
                'name': '包名',
                'desc': '描述',
                'version': '版本号',
                'license': '许可证',
                'homepage': '主页URL',
                'analytics': {...},  # 下载统计
                'dependencies': [...],  # 依赖列表
                ...
            }
        
        示例:
            info = brew.info('drawio')
            print(info['name'])  # 'drawio'
            print(info['desc'])  # 'Desktop application for drawing diagrams'
        """
        # 执行info命令，使用JSON格式输出
        output = self._execute(['info', '--json=v2', package])
        
        # 解析JSON
        data = json.loads(output)
        
        # Homebrew的JSON输出有两种格式：
        # 1. formulae: 命令行工具
        # 2. casks: GUI应用程序
        if data.get('formulae'):
            # Formula类型：命令行工具
            return data['formulae'][0]
        elif data.get('casks'):
            # Cask类型：GUI应用
            return data['casks'][0]
        else:
            # 包不存在
            raise RuntimeError(f"未找到包: {package}")
    
    def install(self, package: str, is_cask: bool = False) -> bool:
        """
        安装软件包
        
        参数:
            package: 包名
            is_cask: 是否为cask包（GUI应用）
        
        返回:
            bool: 安装是否成功
        
        说明:
            执行 brew install [--cask] <package> 命令。
            Cask用于安装GUI应用，Formula用于安装命令行工具。
        
        超时设置:
            安装命令可能需要下载大文件，设置5分钟超时。
        
        示例:
            # 安装命令行工具
            brew.install('wget')
            
            # 安装GUI应用
            brew.install('drawio', is_cask=True)
        """
        try:
            # 构建安装命令参数
            args = ['install']
            
            # 如果是cask包，添加--cask参数
            if is_cask:
                args.append('--cask')
            
            args.append(package)
            
            # 执行安装命令
            # timeout=300: 5分钟超时（下载可能较慢）
            self._execute(args, timeout=300)
            
            # 安装成功
            logger.info(f"成功安装: {package}")
            return True
            
        except RuntimeError as e:
            # 安装失败
            logger.error(f"安装失败: {e}")
            return False
    
    def list_installed(self) -> List[str]:
        """
        列出已安装的软件包
        
        返回:
            List[str]: 已安装的包名列表
        
        说明:
            执行 brew list --formula 命令，
            获取所有已安装的formula包。
        
        注意:
            这里只列出formula包，不包括cask包。
            如需cask包列表，使用 brew list --cask
        
        示例:
            installed = brew.list_installed()
            if 'wget' in installed:
                print("wget已安装")
        """
        # 执行list命令
        output = self._execute(['list', '--formula'])
        
        # 解析输出：每行一个包名
        packages = [
            line.strip() 
            for line in output.split('\n') 
            if line.strip()
        ]
        
        logger.debug(f"已安装{len(packages)}个包")
        
        return packages


# 模块级全局实例
# 其他模块可以直接导入使用: from infrastructure.brew_executor import brew
brew = BrewExecutor()
