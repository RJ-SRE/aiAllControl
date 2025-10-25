"""
软件包仓储层 - Package Repository

设计思想：Repository模式
- 为Service层提供统一的数据访问接口
- 封装Homebrew API调用和数据转换逻辑
- 实现透明的缓存管理，提升性能

职责：
1. 搜索软件包（带缓存）
2. 获取包详细信息（带缓存）
3. 列出已安装的包
4. 数据格式转换（Homebrew JSON → Package实体）
5. 缓存生命周期管理

缓存策略：
- 搜索结果缓存：TTL = 配置的cache_ttl（默认3600秒）
- 包信息缓存：TTL = 配置的cache_ttl（默认3600秒）
- 缓存位置：~/.macmind/cache/
- 缓存格式：JSON文件

错误处理：
- 缓存读取失败：自动回退到API调用
- API调用失败：返回None或空列表，记录错误日志
- 数据转换失败：记录警告并跳过该条目

使用示例：
    from repository.package_repository import PackageRepository
    
    repo = PackageRepository()
    
    # 搜索软件包
    names = repo.search('drawing')
    
    # 获取详细信息
    package = repo.get_package_info('drawio')
    if package:
        print(f"找到: {package.name} - {package.description}")
    
    # 列出已安装
    installed = repo.list_installed()
    print(f"已安装 {len(installed)} 个软件包")
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from domain.package import Package, PackageType, LicenseType
from infrastructure.brew_executor import brew
from infrastructure.logger import logger
from infrastructure.config import config


class PackageRepository:
    """
    软件包仓储 - Repository Pattern
    
    属性：
        cache_dir: 缓存目录路径 (~/.macmind/cache/)
        cache_ttl: 缓存有效期（秒）
        _installed_cache: 已安装包的内存缓存
    
    设计说明：
        Repository模式将数据访问逻辑集中管理，提供统一的查询接口。
        Service层不需要知道数据来自API还是缓存，只需调用Repository的方法。
        
        缓存采用两级设计：
        1. 文件缓存：持久化到磁盘，重启后仍然有效
        2. 内存缓存：已安装包列表，避免重复调用brew list命令
    
    性能优化：
        - 搜索结果缓存：减少brew search调用
        - 包信息缓存：减少brew info调用
        - TTL机制：自动清理过期缓存
        - 批量查询：一次性获取多个包的信息
    """
    
    def __init__(self):
        """
        初始化PackageRepository
        
        创建缓存目录，加载配置参数。
        不会立即调用任何外部API，延迟加载。
        """
        self.cache_dir = Path.home() / '.macmind' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_ttl = config.get('cache_ttl', 3600)
        
        self._installed_cache: Optional[Set[str]] = None
        
        logger.debug(f"PackageRepository初始化完成，缓存目录: {self.cache_dir}")
    
    def search(self, keyword: str) -> List[str]:
        """
        搜索软件包（带缓存）
        
        参数：
            keyword: 搜索关键词（如 'drawing', 'video editor'等）
        
        返回：
            List[str]: 匹配的软件包名称列表
        
        缓存策略：
            - 缓存key: search_{keyword}.json
            - TTL: 配置的cache_ttl
            - 缓存命中：直接返回缓存结果
            - 缓存未命中或过期：调用brew search，更新缓存
        
        示例：
            repo.search('drawing')
            # ['drawio', 'krita', 'gimp', ...]
        """
        if not keyword or not keyword.strip():
            logger.warning("搜索关键词为空")
            return []
        
        keyword = keyword.strip().lower()
        cache_file = self.cache_dir / f"search_{keyword}.json"
        
        if self._is_cache_valid(cache_file):
            logger.debug(f"命中搜索缓存: {keyword}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取搜索缓存失败: {e}，回退到API调用")
        
        try:
            logger.info(f"搜索软件包: {keyword}")
            results = brew.search(keyword)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f)
            
            logger.debug(f"搜索成功，找到 {len(results)} 个结果")
            return results
            
        except RuntimeError as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def get_package_info(self, package_name: str) -> Optional[Package]:
        """
        获取软件包详细信息（带缓存）
        
        参数：
            package_name: 软件包名称（如 'drawio', 'vim'）
        
        返回：
            Package: Package实体对象，如果未找到则返回None
        
        数据流：
            1. 检查缓存是否有效
            2. 缓存命中：反序列化为Package对象
            3. 缓存未命中：调用brew info获取数据
            4. 数据转换：Homebrew JSON → Package实体
            5. 更新缓存：序列化Package对象
        
        缓存策略：
            - 缓存key: info_{package_name}.json
            - TTL: 配置的cache_ttl
        
        错误处理：
            - 包不存在：返回None
            - API调用失败：返回None，记录错误日志
            - 数据转换失败：返回None，记录错误日志
        
        示例：
            package = repo.get_package_info('drawio')
            if package:
                print(f"{package.name}: {package.description}")
                print(f"许可证: {package.license.value}")
        """
        if not package_name or not package_name.strip():
            logger.warning("包名为空")
            return None
        
        package_name = package_name.strip()
        cache_file = self.cache_dir / f"info_{package_name}.json"
        
        if self._is_cache_valid(cache_file):
            logger.debug(f"命中包信息缓存: {package_name}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._dict_to_package(data)
            except Exception as e:
                logger.warning(f"读取包信息缓存失败: {e}，回退到API调用")
        
        try:
            logger.info(f"获取包信息: {package_name}")
            brew_data = brew.info(package_name)
            
            package = self._brew_to_package(brew_data)
            
            is_installed = self._check_if_installed(package_name)
            package.is_installed = is_installed
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._package_to_dict(package), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"包信息获取成功: {package.name}")
            return package
            
        except RuntimeError as e:
            logger.error(f"获取包信息失败 ({package_name}): {e}")
            return None
        except Exception as e:
            logger.error(f"处理包信息时发生错误 ({package_name}): {e}", exc_info=True)
            return None
    
    def list_installed(self) -> List[str]:
        """
        列出已安装的软件包
        
        返回：
            List[str]: 已安装的包名称列表
        
        缓存策略：
            - 使用内存缓存（_installed_cache）
            - 只在首次调用时查询brew list
            - 后续调用直接返回缓存结果
            - 可通过refresh_installed_cache()刷新
        
        性能优化：
            brew list命令可能比较慢（特别是安装了很多软件时），
            因此使用内存缓存避免重复调用。
        
        示例：
            installed = repo.list_installed()
            print(f"已安装 {len(installed)} 个软件包")
        """
        if self._installed_cache is not None:
            logger.debug("使用已安装包的内存缓存")
            return list(self._installed_cache)
        
        return self.refresh_installed_cache()
    
    def refresh_installed_cache(self) -> List[str]:
        """
        刷新已安装包的缓存
        
        返回：
            List[str]: 已安装的包名称列表
        
        使用场景：
            - 安装或卸载软件后，调用此方法刷新缓存
            - 确保list_installed()返回最新数据
        
        示例：
            repo.refresh_installed_cache()
            installed = repo.list_installed()  # 获取最新的安装列表
        """
        try:
            logger.info("刷新已安装包列表")
            installed = brew.list_installed()
            self._installed_cache = set(installed)
            logger.debug(f"已安装 {len(installed)} 个软件包")
            return installed
        except RuntimeError as e:
            logger.error(f"获取已安装包列表失败: {e}")
            self._installed_cache = set()
            return []
    
    def clear_cache(self):
        """
        清空所有缓存
        
        清空文件缓存和内存缓存。
        适用于调试或强制刷新数据的场景。
        
        示例：
            repo.clear_cache()
            # 下次查询将重新调用API
        """
        logger.info("清空缓存")
        
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败 ({cache_file}): {e}")
        
        self._installed_cache = None
        logger.info("缓存已清空")
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """
        检查缓存文件是否有效
        
        参数：
            cache_file: 缓存文件路径
        
        返回：
            bool: 缓存有效返回True，否则返回False
        
        有效条件：
            1. 文件存在
            2. 文件修改时间在TTL范围内
        
        实现细节：
            使用文件的mtime（修改时间）判断缓存年龄。
            如果 (当前时间 - mtime) < cache_ttl，则缓存有效。
        """
        if not cache_file.exists():
            return False
        
        try:
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_seconds = (datetime.now() - mtime).total_seconds()
            
            is_valid = age_seconds < self.cache_ttl
            
            if not is_valid:
                logger.debug(f"缓存已过期: {cache_file.name} (年龄: {age_seconds:.0f}秒)")
            
            return is_valid
            
        except Exception as e:
            logger.warning(f"检查缓存有效性失败: {e}")
            return False
    
    def _brew_to_package(self, brew_data: Dict[str, Any]) -> Package:
        """
        将Homebrew数据转换为Package实体
        
        参数：
            brew_data: brew info --json=v2 返回的字典数据
        
        返回：
            Package: 转换后的Package实体
        
        数据映射：
            Homebrew字段 → Package字段
            - name → name
            - desc → description
            - version/versions → version
            - license → license（需要映射到LicenseType枚举）
            - homepage → homepage
            - analytics → download_count
            - dependencies/dependents → dependencies
        
        类型转换：
            - 包类型判断：存在'cask'字段 → CASK，否则 → FORMULA
            - 许可证映射：字符串 → LicenseType枚举
            - 下载量提取：从analytics.install字段获取
        
        错误处理：
            - 必填字段缺失：使用默认值（如空字符串）
            - 可选字段缺失：返回None或空列表
            - 类型转换失败：使用默认值并记录警告
        """
        package_type = PackageType.CASK if 'cask' in brew_data.get('tap', '') or 'token' in brew_data else PackageType.FORMULA
        
        license_str = brew_data.get('license', 'Unknown')
        if isinstance(license_str, list):
            license_str = license_str[0] if license_str else 'Unknown'
        
        license_type = self._parse_license(license_str)
        
        version = brew_data.get('version')
        if not version:
            versions = brew_data.get('versions', {})
            version = versions.get('stable') or versions.get('head') or 'unknown'
        
        download_count = 0
        analytics = brew_data.get('analytics', {})
        if analytics:
            install_data = analytics.get('install', {}) or analytics.get('install_on_request', {})
            if install_data:
                thirty_day = install_data.get('30d', {})
                if isinstance(thirty_day, dict):
                    download_count = thirty_day.get('count', 0) or thirty_day.get('total', 0)
        
        last_updated = None
        if 'updated_at' in brew_data:
            try:
                last_updated = datetime.fromisoformat(brew_data['updated_at'].replace('Z', '+00:00'))
            except Exception as e:
                logger.debug(f"解析更新时间失败: {e}")
        
        dependencies = brew_data.get('dependencies', [])
        if not isinstance(dependencies, list):
            dependencies = []
        
        package = Package(
            name=brew_data.get('name') or brew_data.get('token', 'unknown'),
            description=brew_data.get('desc', '') or brew_data.get('name', ''),
            package_type=package_type,
            version=version,
            license=license_type,
            homepage=brew_data.get('homepage'),
            download_count=download_count,
            last_updated=last_updated,
            dependencies=dependencies,
            is_installed=False
        )
        
        return package
    
    def _parse_license(self, license_str: str) -> LicenseType:
        """
        将许可证字符串映射到LicenseType枚举
        
        参数：
            license_str: 许可证字符串（如 'MIT', 'Apache-2.0'）
        
        返回：
            LicenseType: 对应的枚举值
        
        映射规则：
            - 精确匹配：'MIT' → LicenseType.MIT
            - 大小写不敏感：'mit' → LicenseType.MIT
            - 部分匹配：'Apache 2.0' → LicenseType.APACHE_2_0
            - 未知类型：返回 LicenseType.UNKNOWN
        
        特殊处理：
            - 'Proprietary' / 'Commercial' → LicenseType.PROPRIETARY
            - 'BSD-2-Clause' / 'BSD-3-Clause' → LicenseType.BSD
        """
        if not license_str or license_str == 'Unknown':
            return LicenseType.UNKNOWN
        
        license_upper = license_str.upper().replace(' ', '-').replace('_', '-')
        
        if 'MIT' in license_upper:
            return LicenseType.MIT
        elif 'APACHE' in license_upper or 'APACHE-2' in license_upper:
            return LicenseType.APACHE_2_0
        elif 'GPL' in license_upper or 'GPL-3' in license_upper:
            return LicenseType.GPL_3_0
        elif 'BSD' in license_upper:
            return LicenseType.BSD
        elif 'PROPRIETARY' in license_upper or 'COMMERCIAL' in license_upper:
            return LicenseType.PROPRIETARY
        else:
            logger.debug(f"未知许可证类型: {license_str}")
            return LicenseType.UNKNOWN
    
    def _check_if_installed(self, package_name: str) -> bool:
        """
        检查软件包是否已安装
        
        参数：
            package_name: 软件包名称
        
        返回：
            bool: 已安装返回True，否则返回False
        
        实现：
            使用已安装包的内存缓存进行快速查询。
            如果缓存未初始化，会自动调用list_installed()。
        """
        if self._installed_cache is None:
            self.list_installed()
        
        return package_name in self._installed_cache if self._installed_cache else False
    
    def _package_to_dict(self, package: Package) -> Dict[str, Any]:
        """
        将Package实体转换为字典（用于缓存序列化）
        
        参数：
            package: Package实体对象
        
        返回：
            Dict: 可序列化的字典
        
        类型转换：
            - PackageType枚举 → 字符串
            - LicenseType枚举 → 字符串
            - datetime → ISO格式字符串
        
        使用场景：
            保存到缓存文件前需要将Package对象转换为JSON可序列化的格式。
        """
        return {
            'name': package.name,
            'description': package.description,
            'type': package.package_type.value,
            'version': package.version,
            'license': package.license.value,
            'homepage': package.homepage,
            'download_count': package.download_count,
            'last_updated': package.last_updated.isoformat() if package.last_updated else None,
            'dependencies': package.dependencies,
            'is_installed': package.is_installed
        }
    
    def _dict_to_package(self, data: Dict[str, Any]) -> Package:
        """
        将字典转换为Package实体（用于缓存反序列化）
        
        参数：
            data: 包含Package数据的字典
        
        返回：
            Package: 重建的Package实体
        
        类型转换：
            - 字符串 → PackageType枚举
            - 字符串 → LicenseType枚举
            - ISO格式字符串 → datetime
        
        错误处理：
            - 枚举值不存在：使用默认值
            - 日期解析失败：返回None
            - 必填字段缺失：抛出KeyError
        
        使用场景：
            从缓存文件读取后需要将字典数据转换回Package对象。
        """
        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except Exception as e:
                logger.debug(f"解析缓存中的更新时间失败: {e}")
        
        return Package(
            name=data['name'],
            description=data['description'],
            package_type=PackageType(data['type']),
            version=data.get('version'),
            license=LicenseType(data.get('license', 'Unknown')),
            homepage=data.get('homepage'),
            download_count=data.get('download_count', 0),
            last_updated=last_updated,
            dependencies=data.get('dependencies', []),
            is_installed=data.get('is_installed', False)
        )
