"""
软件包服务层 - Package Service

核心业务逻辑的实现，协调Repository、Domain和Infrastructure层。

设计思想：Service模式 + 门面模式 (Facade Pattern)
- Service模式：封装业务逻辑，协调多个组件
- 门面模式：为复杂子系统提供简单统一的接口

核心业务流程：
1. 智能搜索：用户输入 → AI分析 → 搜索 → 智能排序 → 返回推荐列表
2. 安装软件：获取包信息 → 检查是否已安装 → 安装 → 刷新缓存
3. 卸载软件：检查是否已安装 → 卸载 → 刷新缓存
4. 列出已安装：获取安装列表 → 获取详细信息 → 返回Package列表

使用示例:
    from service.package_service import PackageService
    
    service = PackageService()
    
    # 智能搜索
    packages = service.search_packages("帮我找一个绘图软件")
    for pkg in packages:
        print(f"{pkg.name}: {pkg.description}")
    
    # 安装软件
    success = service.install_package('drawio')
    
    # 列出已安装
    installed = service.list_installed_packages()
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from domain.package import Package
from repository.package_repository import PackageRepository
from infrastructure.ai_client import create_ai_client, AIClient
from infrastructure.brew_executor import brew
from infrastructure.logger import logger
from infrastructure.config import config


@dataclass
class SearchResult:
    """
    搜索结果
    
    属性:
        keyword: 搜索关键词
        intent: 用户意图
        packages: 排序后的软件包列表
        total_count: 总结果数
    """
    keyword: str
    intent: str
    packages: List[Package]
    total_count: int


class PackageService:
    """
    软件包管理服务
    
    属性:
        repository: 软件包仓储（数据访问层）
        ai_client: AI客户端（用于意图分析）
    
    设计说明:
        Service层是业务逻辑的核心，它：
        1. 不直接调用基础设施层（通过Repository隔离）
        2. 使用Domain对象的业务方法（如calculate_score）
        3. 协调多个组件完成复杂业务流程
        4. 提供事务边界和错误处理
    
    依赖关系:
        PackageService → PackageRepository → BrewExecutor
                      → AIClient
                      → Package (Domain)
    """
    
    def __init__(self):
        """
        初始化PackageService
        
        依赖注入:
            - PackageRepository: 数据访问层
            - AIClient: AI意图分析（可选，失败时降级）
        
        设计模式: 依赖注入 (Dependency Injection)
            通过构造函数注入依赖，便于测试和替换实现
        """
        self.repository = PackageRepository()
        
        try:
            self.ai_client: Optional[AIClient] = create_ai_client()
        except Exception as e:
            logger.warning(f"AI客户端初始化失败，将禁用AI功能: {e}")
            self.ai_client = None
        
        logger.debug("PackageService初始化完成")
    
    def search_packages(
        self, 
        user_input: str,
        max_results: Optional[int] = None
    ) -> SearchResult:
        """
        智能搜索软件包
        
        参数:
            user_input: 用户输入的自然语言（如"帮我找一个绘图软件"）
            max_results: 最大返回结果数，默认从配置读取
        
        返回:
            SearchResult: 搜索结果对象
        
        业务流程:
            1. AI分析用户意图，提取关键词
            2. 使用关键词搜索软件包
            3. 批量获取包的详细信息
            4. 智能排序（开源优先、下载量、活跃度）
            5. 限制返回结果数量
        
        智能排序算法:
            使用Package.calculate_score()进行评分:
            - 许可证匹配: 50分（用户偏好）或 30分（开源）
            - 下载量: 0-30分（对数函数）
            - 更新活跃度: 0-20分
            总分: 0-100分
        
        降级策略:
            - AI分析失败 → 直接使用用户输入作为关键词
            - 搜索失败 → 返回空列表
            - 获取详细信息失败 → 跳过该包
        
        示例:
            >>> service = PackageService()
            >>> result = service.search_packages("绘图软件")
            >>> print(f"找到 {result.total_count} 个结果")
            >>> for pkg in result.packages[:5]:
            ...     print(f"- {pkg.name}: {pkg.description}")
        """
        if not user_input or not user_input.strip():
            logger.warning("用户输入为空")
            return SearchResult(
                keyword='',
                intent='',
                packages=[],
                total_count=0
            )
        
        if max_results is None:
            max_results = config.get('max_search_results', 5)
        
        keyword = user_input.strip()
        intent = '搜索'
        
        if self.ai_client:
            try:
                logger.info(f"分析用户意图: {user_input}")
                analysis = self.ai_client.analyze_intent(user_input)
                
                keyword = analysis.get('keyword', user_input)
                intent = analysis.get('intent', '搜索')
                
                logger.debug(f"AI分析结果 - 意图: {intent}, 关键词: {keyword}")
                
            except Exception as e:
                logger.warning(f"AI分析失败，使用原始输入: {e}")
        
        package_names = self.repository.search(keyword)
        
        if not package_names:
            logger.info(f"未找到匹配的软件包: {keyword}")
            return SearchResult(
                keyword=keyword,
                intent=intent,
                packages=[],
                total_count=0
            )
        
        logger.info(f"搜索到 {len(package_names)} 个软件包，正在并发获取详细信息...")
        
        packages = []
        package_list = self.repository.get_package_info_batch(package_names)
        
        for package in package_list:
            if package:
                packages.append(package)
        
        preferred_licenses = config.get('preferred_license', ['MIT', 'Apache-2.0', 'GPL-3.0'])
        
        packages.sort(
            key=lambda p: p.calculate_score(preferred_licenses),
            reverse=True
        )
        
        total_count = len(packages)
        top_packages = packages[:max_results]
        
        logger.info(f"排序完成，返回前 {len(top_packages)} 个结果")
        
        return SearchResult(
            keyword=keyword,
            intent=intent,
            packages=top_packages,
            total_count=total_count
        )
    
    def install_package(
        self,
        package_name: str,
        force: bool = False
    ) -> bool:
        """
        安装软件包
        
        参数:
            package_name: 软件包名称
            force: 是否强制安装（即使已安装）
        
        返回:
            bool: 安装是否成功
        
        业务流程:
            1. 获取包详细信息（检查包是否存在）
            2. 检查是否已安装
            3. 调用brew安装
            4. 刷新已安装包缓存
        
        错误处理:
            - 包不存在 → 返回False，记录错误
            - 已安装且force=False → 返回True，提示已安装
            - 安装失败 → 返回False，记录错误
        
        事务处理:
            安装成功后刷新缓存，确保数据一致性
        
        示例:
            >>> service = PackageService()
            >>> success = service.install_package('drawio')
            >>> if success:
            ...     print("安装成功")
        """
        if not package_name or not package_name.strip():
            logger.warning("包名为空")
            return False
        
        package_name = package_name.strip()
        
        logger.info(f"准备安装软件包: {package_name}")
        
        package = self.repository.get_package_info(package_name)
        if not package:
            logger.error(f"软件包不存在: {package_name}")
            return False
        
        if package.is_installed and not force:
            logger.info(f"软件包已安装: {package_name}")
            return True
        
        is_cask = package.package_type.value == 'cask'
        
        try:
            logger.info(f"正在安装 {package_name} (类型: {package.package_type.value})...")
            
            options = {'is_cask': is_cask} if is_cask else None
            success = brew.install(package_name, options)
            
            if success:
                logger.info(f"安装成功: {package_name}")
                
                self.repository.refresh_installed_cache()
                
                return True
            else:
                logger.error(f"安装失败: {package_name}")
                return False
                
        except Exception as e:
            logger.error(f"安装过程中发生错误: {e}", exc_info=True)
            return False
    
    def uninstall_package(self, package_name: str) -> bool:
        """
        卸载软件包
        
        参数:
            package_name: 软件包名称
        
        返回:
            bool: 卸载是否成功
        
        业务流程:
            1. 检查包是否已安装
            2. 调用brew卸载
            3. 刷新已安装包缓存
        
        错误处理:
            - 包未安装 → 返回True（幂等性）
            - 卸载失败 → 返回False，记录错误
        
        幂等性设计:
            如果包本来就未安装，视为成功，避免报错
        
        示例:
            >>> service = PackageService()
            >>> success = service.uninstall_package('drawio')
            >>> if success:
            ...     print("卸载成功")
        """
        if not package_name or not package_name.strip():
            logger.warning("包名为空")
            return False
        
        package_name = package_name.strip()
        
        logger.info(f"准备卸载软件包: {package_name}")
        
        installed_packages = self.repository.list_installed()
        if package_name not in installed_packages:
            logger.info(f"软件包未安装，无需卸载: {package_name}")
            return True
        
        try:
            logger.info(f"正在卸载 {package_name}...")
            
            success = brew.uninstall(package_name)
            
            if success:
                logger.info(f"卸载成功: {package_name}")
                self.repository.refresh_installed_cache()
                return True
            else:
                logger.error(f"卸载失败: {package_name}")
                return False
            
        except Exception as e:
            logger.error(f"卸载失败: {e}", exc_info=True)
            return False
    
    def list_installed_packages(self) -> List[Package]:
        """
        列出所有已安装的软件包
        
        返回:
            List[Package]: 已安装的Package对象列表
        
        业务流程:
            1. 从Repository获取已安装包名列表
            2. 批量获取每个包的详细信息
            3. 按名称排序
        
        性能优化:
            - Repository层使用内存缓存，避免重复调用brew list
            - 包信息使用文件缓存，减少API调用
        
        错误处理:
            - 获取某个包的详细信息失败 → 跳过该包，继续处理其他包
            - 完全失败 → 返回空列表
        
        示例:
            >>> service = PackageService()
            >>> installed = service.list_installed_packages()
            >>> print(f"已安装 {len(installed)} 个软件包")
            >>> for pkg in installed:
            ...     print(f"- {pkg.name} ({pkg.version})")
        """
        logger.info("列出已安装的软件包")
        
        try:
            package_names = self.repository.list_installed()
            
            if not package_names:
                logger.info("未安装任何软件包")
                return []
            
            logger.debug(f"已安装 {len(package_names)} 个软件包，正在并发获取详细信息...")
            
            packages = []
            package_list = self.repository.get_package_info_batch(package_names)
            
            for package in package_list:
                if package:
                    packages.append(package)
            
            packages.sort(key=lambda p: p.name)
            
            logger.info(f"成功获取 {len(packages)} 个已安装包的详细信息")
            
            return packages
            
        except Exception as e:
            logger.error(f"列出已安装包时发生错误: {e}", exc_info=True)
            return []
    
    def get_package_details(self, package_name: str) -> Optional[Package]:
        """
        获取软件包的详细信息
        
        参数:
            package_name: 软件包名称
        
        返回:
            Package: 包详细信息，不存在返回None
        
        业务流程:
            直接委托给Repository层，提供Service层的统一接口
        
        使用场景:
            Controller层需要展示某个包的详细信息时调用
        
        示例:
            >>> service = PackageService()
            >>> pkg = service.get_package_details('vim')
            >>> if pkg:
            ...     print(f"名称: {pkg.name}")
            ...     print(f"描述: {pkg.description}")
            ...     print(f"许可证: {pkg.license.value}")
        """
        if not package_name or not package_name.strip():
            logger.warning("包名为空")
            return None
        
        logger.debug(f"获取包详细信息: {package_name}")
        
        return self.repository.get_package_info(package_name.strip())
    
    def clear_cache(self):
        """
        清空所有缓存
        
        使用场景:
            - 调试时强制刷新数据
            - 缓存数据异常时重置
        
        影响范围:
            - 搜索结果缓存
            - 包信息缓存
            - 已安装包的内存缓存
        
        示例:
            >>> service = PackageService()
            >>> service.clear_cache()
            >>> # 下次查询将重新调用API
        """
        logger.info("清空Service层缓存")
        self.repository.clear_cache()
