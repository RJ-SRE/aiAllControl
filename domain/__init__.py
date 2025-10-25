"""
Domain Layer (领域模型层)

设计原则:
1. 纯粹的业务逻辑，不依赖外部技术实现
2. 充血模型：实体包含数据和业务逻辑
3. 无外部依赖：只使用Python标准库
4. 高内聚：业务规则封装在实体内部
5. 易于测试：无需mock外部依赖

职责:
- 定义核心业务实体（Package）
- 封装业务规则和验证逻辑
- 提供领域值对象（LicenseType, PackageType）

依赖关系:
- Domain层不依赖任何其他层
- 其他所有层可以依赖Domain层
"""

from domain.package import Package, PackageType, LicenseType

__all__ = ['Package', 'PackageType', 'LicenseType']
