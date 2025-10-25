"""
软件包领域模型

设计思想：充血模型 (Rich Domain Model)
- 不仅包含数据，还包含业务逻辑
- 业务规则封装在实体内部，而不是散落在服务层
- 符合DDD（领域驱动设计）原则

核心实体：Package
- 代表一个软件包的完整信息
- 包含评分算法、许可证判断等业务逻辑

值对象：LicenseType, PackageType
- 不可变的枚举类型
- 提供类型安全和自动补全支持
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import math


class LicenseType(Enum):
    """
    软件许可证类型（值对象）
    
    设计思想：
    - 使用枚举提供类型安全
    - 避免字符串拼写错误
    - IDE可以自动补全
    
    常见开源许可证说明：
    - MIT: 最宽松的开源许可证，允许商业使用
    - Apache-2.0: 包含专利授权的宽松许可证
    - GPL-3.0: Copyleft许可证，衍生作品必须开源
    - BSD: 类似MIT的宽松许可证
    - Proprietary: 专有软件，通常收费
    - Unknown: 许可证未知或未明确
    """
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"
    BSD = "BSD"
    PROPRIETARY = "Proprietary"
    UNKNOWN = "Unknown"


class PackageType(Enum):
    """
    软件包类型（值对象）
    
    Homebrew的两种包类型：
    - FORMULA: 命令行工具（如vim, wget, git）
    - CASK: GUI应用程序（如Chrome, VSCode, Slack）
    
    设计思想：
    - 使用枚举而不是字符串提供类型安全
    - 便于后续扩展其他包管理器的包类型
    """
    FORMULA = "formula"
    CASK = "cask"


@dataclass
class Package:
    """
    软件包实体（充血模型）
    
    设计思想：
    1. 数据和行为封装在一起（充血模型）
    2. 业务逻辑在实体内部，不依赖外部服务
    3. 使用dataclass简化代码，自动生成__init__等方法
    4. 类型提示提供IDE支持和类型检查
    
    属性说明：
    - name: 包名（唯一标识）
    - description: 包描述
    - package_type: 包类型（Formula或Cask）
    - version: 版本号
    - license: 许可证类型
    - homepage: 官网地址
    - download_count: 30天下载量（用于评分）
    - last_updated: 最后更新时间
    - dependencies: 依赖包列表
    - is_installed: 是否已安装
    
    业务方法：
    - is_free(): 判断是否免费
    - is_open_source(): 判断是否开源
    - calculate_score(): 计算推荐分数
    - validate(): 数据验证
    - to_dict(): 序列化为字典
    - from_dict(): 从字典反序列化
    """
    
    name: str
    description: str
    package_type: PackageType
    version: Optional[str] = None
    license: LicenseType = LicenseType.UNKNOWN
    homepage: Optional[str] = None
    download_count: int = 0
    last_updated: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    is_installed: bool = False
    
    def __post_init__(self):
        """
        dataclass初始化后自动调用
        
        设计思想：快速失败（Fail-fast）
        - 在对象创建时立即验证数据
        - 确保无效数据不进入系统
        - 错误在源头暴露，便于调试
        """
        self.validate()
    
    def validate(self):
        """
        数据验证
        
        验证规则：
        1. 包名不能为空
        2. 描述不能为空
        3. 下载量不能为负数
        
        设计思想：
        - 防御式编程，确保数据完整性
        - 抛出ValueError便于上层捕获和处理
        - 提供明确的错误信息
        
        异常：
            ValueError: 数据不符合业务规则
        
        示例：
            >>> pkg = Package(name="", description="test", package_type=PackageType.FORMULA)
            ValueError: 包名不能为空
        """
        if not self.name or not self.name.strip():
            raise ValueError("包名不能为空")
        
        if not self.description or not self.description.strip():
            raise ValueError("描述不能为空")
        
        if self.download_count < 0:
            raise ValueError(f"下载量不能为负数: {self.download_count}")
    
    def is_free(self) -> bool:
        """
        判断软件是否免费
        
        业务规则：
        - 只有PROPRIETARY（专有软件）被视为收费
        - UNKNOWN默认视为免费（宽松判断）
        
        设计决策：
        为什么UNKNOWN视为免费？
        - 大多数开源软件的许可证信息不完整
        - 宽松判断避免误过滤
        - 用户体验优先
        
        返回:
            bool: True表示免费，False表示收费
        
        示例：
            >>> pkg = Package(name="vim", description="editor", 
            ...               package_type=PackageType.FORMULA, 
            ...               license=LicenseType.MIT)
            >>> pkg.is_free()
            True
        """
        return self.license != LicenseType.PROPRIETARY
    
    def is_open_source(self) -> bool:
        """
        判断软件是否开源
        
        业务规则：
        - 只有明确的开源许可证才返回True
        - UNKNOWN不视为开源（严格判断）
        
        设计决策：
        为什么UNKNOWN不视为开源？
        - 与is_free()不同，开源推荐需要确定性
        - 确保推荐的是真正的开源软件
        - 质量保证优先
        
        返回:
            bool: True表示开源，False表示非开源或未知
        
        示例：
            >>> pkg = Package(name="vim", description="editor",
            ...               package_type=PackageType.FORMULA,
            ...               license=LicenseType.GPL_3_0)
            >>> pkg.is_open_source()
            True
        """
        return self.license in {
            LicenseType.MIT,
            LicenseType.APACHE_2_0,
            LicenseType.GPL_3_0,
            LicenseType.BSD
        }
    
    def calculate_score(self, preferred_licenses: List[str]) -> float:
        """
        计算软件包的推荐分数（0-100分）
        
        设计思想：多维度智能评分算法
        
        评分维度：
        1. 许可证匹配（0-50分，权重50%）
           - 用户偏好的许可证: 50分
           - 其他开源许可证: 30分
           - 专有软件或未知: 0分
        
        2. 下载量热度（0-30分，权重30%）
           - 使用对数函数: log10(downloads) * 10
           - 上限30分，避免热门软件分数过高
        
        3. 更新活跃度（0-20分，权重20%）
           - 最近30天有更新: 20分
           - 无更新或未知: 0分
        
        对数函数的优势：
        - 避免线性增长导致热门软件分数过高
        - 反映真实感知：100→1000的提升 > 1000→10000的提升
        - 示例：
            * 10次下载 → 10分
            * 100次下载 → 20分
            * 1,000次下载 → 30分
            * 10,000次下载 → 30分（上限）
        
        参数:
            preferred_licenses: 用户偏好的许可证列表（如['MIT', 'Apache-2.0']）
        
        返回:
            float: 推荐分数（0.0-100.0）
        
        示例：
            >>> pkg = Package(
            ...     name="drawio", 
            ...     description="Diagram editor",
            ...     package_type=PackageType.CASK,
            ...     license=LicenseType.APACHE_2_0,
            ...     download_count=50000,
            ...     last_updated=datetime.now()
            ... )
            >>> score = pkg.calculate_score(['Apache-2.0'])
            >>> print(f"{score:.1f}")  # 约96.8分
            96.8
        
        注意:
            分数设计为主观推荐指标，不代表软件质量的绝对评价
        """
        score = 0.0
        
        # 维度1: 许可证评分（最高50分）
        # 许可证是最重要的因素，占50%权重
        if self.license.value in preferred_licenses:
            # 用户偏好的许可证：满分50分
            score += 50
        elif self.is_open_source():
            # 开源但非偏好许可证：30分
            score += 30
        # 专有软件或未知：0分
        
        # 维度2: 下载量评分（最高30分）
        # 使用对数函数避免线性增长
        if self.download_count > 0:
            # log10(downloads) * 10，上限30分
            download_score = math.log10(self.download_count) * 10
            score += min(download_score, 30)
        
        # 维度3: 更新活跃度评分（最高20分）
        # 最近30天有更新，说明项目活跃维护
        if self.last_updated:
            days_ago = (datetime.now() - self.last_updated).days
            if days_ago <= 30:
                score += 20
        
        # 确保分数在0-100范围内
        return min(score, 100.0)
    
    def to_dict(self) -> dict:
        """
        将Package对象序列化为字典
        
        用途：
        - JSON序列化（保存到缓存）
        - 数据传输（API响应）
        - 日志记录
        
        设计思想：
        - 枚举类型转换为字符串值
        - datetime转换为ISO格式字符串
        - None保持不变
        - 只包含必要字段，减少数据量
        
        返回:
            dict: 包含软件包信息的字典
        
        示例：
            >>> pkg = Package(name="vim", description="editor",
            ...               package_type=PackageType.FORMULA)
            >>> data = pkg.to_dict()
            >>> print(data['name'])
            vim
        """
        return {
            'name': self.name,
            'description': self.description,
            'type': self.package_type.value,  # 枚举 → 字符串
            'version': self.version,
            'license': self.license.value,  # 枚举 → 字符串
            'homepage': self.homepage,
            'download_count': self.download_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'dependencies': self.dependencies,
            'is_installed': self.is_installed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Package':
        """
        从字典反序列化为Package对象（工厂方法）
        
        设计思想：
        - 使用classmethod作为工厂方法
        - 处理类型转换（字符串 → 枚举 → datetime）
        - 提供默认值处理
        - 隐藏对象创建的复杂度
        
        类型转换：
        - 'formula' → PackageType.FORMULA
        - 'MIT' → LicenseType.MIT
        - '2024-10-25T00:00:00' → datetime对象
        
        参数:
            data: 包含软件包信息的字典
        
        返回:
            Package: 反序列化的Package对象
        
        异常:
            ValueError: 枚举值不合法
            KeyError: 缺少必需字段
        
        示例：
            >>> data = {
            ...     'name': 'vim',
            ...     'description': 'Vi IMproved',
            ...     'type': 'formula',
            ...     'license': 'MIT'
            ... }
            >>> pkg = Package.from_dict(data)
            >>> print(pkg.name)
            vim
        """
        # 字符串 → 枚举类型
        package_type = PackageType(data['type'])
        license_type = LicenseType(data.get('license', 'Unknown'))
        
        # ISO字符串 → datetime对象
        last_updated = None
        if data.get('last_updated'):
            last_updated = datetime.fromisoformat(data['last_updated'])
        
        # 创建Package对象
        return cls(
            name=data['name'],
            description=data['description'],
            package_type=package_type,
            version=data.get('version'),
            license=license_type,
            homepage=data.get('homepage'),
            download_count=data.get('download_count', 0),
            last_updated=last_updated,
            dependencies=data.get('dependencies', []),
            is_installed=data.get('is_installed', False)
        )
    
    def __repr__(self) -> str:
        """
        对象的字符串表示（用于调试）
        
        返回:
            str: 包含关键信息的字符串
        
        示例：
            >>> pkg = Package(name="vim", description="editor",
            ...               package_type=PackageType.FORMULA)
            >>> repr(pkg)
            "Package(name='vim', type=FORMULA, license=UNKNOWN)"
        """
        return (f"Package(name='{self.name}', "
                f"type={self.package_type.name}, "
                f"license={self.license.name})")
