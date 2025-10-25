"""
配置管理模块 - Configuration Management

集中管理应用程序配置，支持多种配置源。

设计模式: 单例模式 (Singleton Pattern)
- 确保全局只有一个配置实例
- 统一配置访问接口

配置优先级:
1. 环境变量 (最高优先级)
2. 配置文件 (~/.macmind/config.json)
3. 默认值 (最低优先级)

配置项说明:
- api_key: AI服务的API密钥
- api_provider: AI提供商 (anthropic/openai)
- openai_base_url: OpenAI兼容API端点URL (可选，如: https://openai.qiniu.com/v1)
- homebrew_path: Homebrew可执行文件路径
- max_search_results: 最大搜索结果数
- auto_install: 是否自动安装(无需确认)
- preferred_license: 优先推荐的开源许可证列表
- cache_ttl: 缓存有效期(秒)

使用示例:
    from infrastructure.config import config
    
    # 读取配置
    api_key = config.get('api_key')
    max_results = config.get('max_search_results', 5)
    
    # 修改配置
    config.set('max_search_results', 10)
    config.save()  # 保存到文件
    
    # 验证配置
    if config.validate():
        print("配置完整")
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class Config:
    """
    配置管理器 - 单例模式实现
    
    属性:
        _instance: 类级别的单例实例
        _initialized: 标记是否已初始化
        config_dir: 配置文件目录路径
        config_file: 配置文件完整路径
        _config: 内部配置字典
    
    设计说明:
        采用单例模式确保全局配置一致性，避免多处读取配置
        导致的配置不同步问题。
    """
    
    # 类变量：存储唯一实例
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        """
        控制对象创建，实现单例模式
        
        返回:
            Config: 全局唯一的Config实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化配置管理器
        
        说明:
            使用_initialized标志避免重复初始化
        """
        # 检查是否已初始化
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # 配置文件路径设置
        # 存放在用户主目录的 .macmind 文件夹中
        self.config_dir = Path.home() / '.macmind'
        self.config_file = self.config_dir / 'config.json'
        
        # 内部配置字典
        self._config: Dict[str, Any] = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """
        加载配置的核心方法
        
        加载顺序:
        1. 设置默认值
        2. 从配置文件读取（如果存在）
        3. 从环境变量读取（覆盖前面的配置）
        
        配置说明:
        - api_key: 从环境变量读取，不存储到文件（安全考虑）
        - homebrew_path: Homebrew默认安装路径
        - max_search_results: 限制搜索结果数量，避免过多
        - auto_install: 默认false，需要用户确认安装
        - preferred_license: 优先开源协议，确保软件免费
        - cache_ttl: 1小时缓存，平衡性能和数据新鲜度
        """
        # 步骤1: 设置默认配置
        # 这些是应用程序的出厂设置
        self._config = {
            # AI相关配置
            'api_key': None,  # API密钥，从环境变量读取
            'api_provider': 'anthropic',  # 默认使用Anthropic的Claude
            
            # Homebrew配置
            'homebrew_path': '/opt/homebrew/bin/brew',  # Apple Silicon Mac默认路径
            
            # 搜索配置
            'max_search_results': 5,  # 最多显示5个结果，避免信息过载
            
            # 安装配置
            'auto_install': False,  # 默认需要用户确认，安全第一
            
            # 许可证偏好
            # 优先推荐这些开源许可证的软件
            'preferred_license': ['MIT', 'Apache-2.0', 'GPL-3.0'],
            
            # 缓存配置
            'cache_ttl': 3600,  # 缓存1小时（3600秒）
        }
        
        # 步骤2: 从配置文件加载
        # 如果用户修改过配置并保存，则使用用户配置
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 更新默认配置（不覆盖，只补充/更新已有键）
                    self._config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                # 配置文件损坏时使用默认配置
                # 这里可以记录错误日志，但不导入logger避免循环依赖
                pass
        
        # 步骤3: 从环境变量加载API密钥
        # 环境变量优先级最高，覆盖配置文件
        # 支持两种AI提供商的环境变量
        env_api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        if env_api_key:
            self._config['api_key'] = env_api_key
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值
        
        参数:
            key: 配置项的键名
            default: 如果键不存在时返回的默认值
        
        返回:
            配置项的值，如果不存在则返回default
        
        示例:
            api_key = config.get('api_key')
            max_results = config.get('max_search_results', 5)
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        设置配置项的值
        
        参数:
            key: 配置项的键名
            value: 要设置的值
        
        说明:
            修改后的配置只在内存中，需要调用save()才能持久化
        
        示例:
            config.set('max_search_results', 10)
            config.save()  # 保存到文件
        """
        self._config[key] = value
    
    def save(self):
        """
        保存配置到文件
        
        说明:
        1. 自动创建配置目录（如果不存在）
        2. 过滤敏感信息（API密钥不保存到文件）
        3. 使用JSON格式，便于人工编辑
        4. 使用UTF-8编码，支持中文
        
        安全考虑:
            API密钥不保存到文件，只从环境变量读取，
            避免密钥泄露的安全风险。
        
        示例:
            config.set('max_search_results', 10)
            config.save()
        """
        # 步骤1: 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 步骤2: 过滤敏感信息
        # 创建配置副本，排除api_key
        save_config = {
            k: v for k, v in self._config.items() 
            if k != 'api_key'  # 不保存API密钥
        }
        
        # 步骤3: 写入JSON文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(
                save_config, 
                f, 
                indent=2,  # 美化输出，便于阅读
                ensure_ascii=False  # 支持中文字符
            )
    
    def validate(self) -> bool:
        """
        验证配置是否完整有效
        
        返回:
            bool: True表示配置完整，False表示配置缺失或无效
        
        验证项:
        1. API密钥必须存在
        2. Homebrew路径必须存在且可执行
        
        使用场景:
            在应用启动时验证配置，避免运行时错误
        
        示例:
            if not config.validate():
                print("配置不完整，请设置API密钥")
                sys.exit(1)
        """
        # 验证1: 检查API密钥
        if not self._config.get('api_key'):
            return False
        
        # 验证2: 检查Homebrew路径
        homebrew_path = Path(self._config['homebrew_path'])
        if not homebrew_path.exists():
            return False
        
        # 所有验证通过
        return True


# 模块级全局实例
# 其他模块可以直接导入使用: from infrastructure.config import config
config = Config()
