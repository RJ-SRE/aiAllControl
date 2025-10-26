"""
会话管理模块 - Conversation Manager

管理AI对话的历史记录和上下文,支持多轮对话和会话持久化。

设计模式: 单例模式 + 策略模式
- 单例模式: 确保全局只有一个会话管理器
- 策略模式: 支持不同的上下文管理策略

核心功能:
1. 对话历史管理 - 添加、获取、清除消息
2. 上下文窗口控制 - 限制历史消息数量
3. 会话持久化 - 保存和加载会话
4. Token计数 - 估算上下文长度

使用示例:
    from infrastructure.conversation import conversation_manager
    
    # 添加消息
    conversation_manager.add_user_message("帮我找一个绘图软件")
    conversation_manager.add_assistant_message("我推荐使用drawio")
    
    # 获取上下文
    context = conversation_manager.get_context()
    
    # 清除历史
    conversation_manager.clear()
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from infrastructure.logger import logger
from domain.exceptions import ConversationError


class ConversationManager:
    """
    会话管理器 - 单例模式实现
    
    属性:
        _instance: 类级别的单例实例
        _initialized: 标记是否已初始化
        history: 对话历史列表
        max_history: 最大历史消息数量
        session_file: 会话持久化文件路径
    
    设计说明:
        采用单例模式确保全局只有一个会话管理器,
        维护一致的对话状态。
    """
    
    _instance: Optional['ConversationManager'] = None
    
    def __new__(cls):
        """
        控制对象创建,实现单例模式
        
        返回:
            ConversationManager: 全局唯一的会话管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_history: int = 50):
        """
        初始化会话管理器
        
        参数:
            max_history: 最大保留的历史消息数量(默认50条)
        
        说明:
            使用_initialized标志避免重复初始化
        """
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
        
        self.session_dir = Path.home() / '.macmind' / 'sessions'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / 'current_session.json'
        
        logger.debug(f"ConversationManager初始化完成,最大历史记录: {max_history}")
    
    def add_user_message(self, content: str):
        """
        添加用户消息到历史记录
        
        参数:
            content: 用户消息内容
        
        示例:
            conversation_manager.add_user_message("帮我找一个绘图软件")
        """
        if not content or not content.strip():
            logger.warning("用户消息为空,跳过添加")
            return
        
        self.history.append({
            "role": "user",
            "content": content.strip(),
            "timestamp": datetime.now().isoformat()
        })
        
        self._trim_history()
        logger.debug(f"添加用户消息: {content[:50]}...")
    
    def add_assistant_message(self, content: str):
        """
        添加助手消息到历史记录
        
        参数:
            content: 助手消息内容
        
        示例:
            conversation_manager.add_assistant_message("我推荐使用drawio")
        """
        if not content or not content.strip():
            logger.warning("助手消息为空,跳过添加")
            return
        
        self.history.append({
            "role": "assistant",
            "content": content.strip(),
            "timestamp": datetime.now().isoformat()
        })
        
        self._trim_history()
        logger.debug(f"添加助手消息: {content[:50]}...")
    
    def add_system_message(self, content: str):
        """
        添加系统消息到历史记录
        
        参数:
            content: 系统消息内容
        
        说明:
            系统消息用于设置AI的行为和角色
        
        示例:
            conversation_manager.add_system_message("你是一个软件包管理助手")
        """
        if not content or not content.strip():
            logger.warning("系统消息为空,跳过添加")
            return
        
        self.history.append({
            "role": "system",
            "content": content.strip(),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.debug(f"添加系统消息: {content[:50]}...")
    
    def get_context(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取对话上下文
        
        参数:
            max_messages: 最多返回多少条消息(None=使用max_history)
        
        返回:
            List[Dict]: 对话历史列表,每条消息包含role和content
        
        说明:
            返回最近的N条消息,用于构建AI的上下文
            只返回role和content字段,不包括timestamp
        
        示例:
            context = conversation_manager.get_context(max_messages=10)
            # [
            #     {"role": "user", "content": "帮我找一个绘图软件"},
            #     {"role": "assistant", "content": "我推荐使用drawio"}
            # ]
        """
        if max_messages is None:
            max_messages = self.max_history
        
        recent_messages = self.history[-max_messages:]
        
        context = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent_messages
        ]
        
        logger.debug(f"获取上下文,消息数: {len(context)}")
        return context
    
    def clear(self):
        """
        清空对话历史
        
        使用场景:
            - 开始新的对话会话
            - 上下文过长时重置
            - 调试和测试
        
        示例:
            conversation_manager.clear()
        """
        self.history.clear()
        logger.info("对话历史已清空")
    
    def get_message_count(self) -> int:
        """
        获取当前历史消息数量
        
        返回:
            int: 历史消息数量
        
        示例:
            count = conversation_manager.get_message_count()
            print(f"当前有 {count} 条消息")
        """
        return len(self.history)
    
    def save_session(self, filename: Optional[str] = None):
        """
        保存会话到文件
        
        参数:
            filename: 文件名(可选,默认使用current_session.json)
        
        说明:
            将对话历史序列化为JSON并保存到磁盘
        
        示例:
            conversation_manager.save_session()
            conversation_manager.save_session("my_session.json")
        """
        try:
            if filename:
                session_file = self.session_dir / filename
            else:
                session_file = self.session_file
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'history': self.history,
                    'created_at': datetime.now().isoformat(),
                    'message_count': len(self.history)
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"会话已保存: {session_file}")
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}", exc_info=True)
            raise ConversationError(
                "会话保存失败",
                detail=str(e),
                context={'file': str(session_file)}
            )
    
    def load_session(self, filename: Optional[str] = None):
        """
        从文件加载会话
        
        参数:
            filename: 文件名(可选,默认使用current_session.json)
        
        说明:
            从磁盘读取JSON文件并恢复对话历史
        
        示例:
            conversation_manager.load_session()
            conversation_manager.load_session("my_session.json")
        """
        try:
            if filename:
                session_file = self.session_dir / filename
            else:
                session_file = self.session_file
            
            if not session_file.exists():
                logger.warning(f"会话文件不存在: {session_file}")
                return
            
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get('history', [])
            
            logger.info(f"会话已加载: {session_file}, 消息数: {len(self.history)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"会话文件格式错误: {e}")
            raise ConversationError(
                "会话文件格式错误",
                detail=str(e),
                context={'file': str(session_file)}
            )
        except Exception as e:
            logger.error(f"加载会话失败: {e}", exc_info=True)
            raise ConversationError(
                "会话加载失败",
                detail=str(e),
                context={'file': str(session_file)}
            )
    
    def _trim_history(self):
        """
        修剪历史记录,保持在最大限制内
        
        说明:
            当历史记录超过max_history时,删除最旧的消息
            系统消息不会被删除
        """
        if len(self.history) <= self.max_history:
            return
        
        system_messages = [msg for msg in self.history if msg['role'] == 'system']
        other_messages = [msg for msg in self.history if msg['role'] != 'system']
        
        if len(other_messages) > self.max_history:
            other_messages = other_messages[-(self.max_history - len(system_messages)):]
        
        self.history = system_messages + other_messages
        
        logger.debug(f"历史记录已修剪,当前消息数: {len(self.history)}")
    
    def estimate_tokens(self) -> int:
        """
        估算当前上下文的Token数量
        
        返回:
            int: 估算的Token数量
        
        说明:
            简单估算: 中文按2个字符=1个token,英文按4个字符=1个token
            实际token数量取决于具体的tokenizer
        
        示例:
            tokens = conversation_manager.estimate_tokens()
            print(f"当前上下文约 {tokens} 个token")
        """
        total_chars = sum(len(msg['content']) for msg in self.history)
        
        estimated_tokens = total_chars // 3
        
        return estimated_tokens
    
    def get_last_user_message(self) -> Optional[str]:
        """
        获取最后一条用户消息
        
        返回:
            Optional[str]: 最后一条用户消息的内容,如果没有则返回None
        
        示例:
            last_msg = conversation_manager.get_last_user_message()
            if last_msg:
                print(f"上次你问: {last_msg}")
        """
        for msg in reversed(self.history):
            if msg['role'] == 'user':
                return msg['content']
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """
        获取最后一条助手消息
        
        返回:
            Optional[str]: 最后一条助手消息的内容,如果没有则返回None
        
        示例:
            last_msg = conversation_manager.get_last_assistant_message()
            if last_msg:
                print(f"我上次回答: {last_msg}")
        """
        for msg in reversed(self.history):
            if msg['role'] == 'assistant':
                return msg['content']
        return None


conversation_manager = ConversationManager()
