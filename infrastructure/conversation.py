"""
会话管理模块 - Conversation Manager

管理AI对话历史,支持上下文记忆和会话持久化。

设计模式: 单例模式
- 确保全局只有一个会话管理器实例
- 所有对话共享同一个历史记录

主要功能:
1. 对话历史管理 - 添加、获取、清除消息
2. 上下文窗口控制 - 限制历史消息数量,避免超出token限制
3. 会话持久化 - 保存/加载会话到文件
4. Token估算 - 估算当前会话的token使用量
5. 会话统计 - 消息数量、轮次统计

使用示例:
    from infrastructure.conversation import ConversationManager
    
    # 获取会话管理器实例
    manager = ConversationManager()
    
    # 添加用户消息
    manager.add_user_message("帮我找一个绘图软件")
    
    # 添加AI响应
    manager.add_assistant_message("我推荐drawio")
    
    # 获取上下文(用于AI调用)
    context = manager.get_context()
    
    # 保存会话
    manager.save_session()
    
    # 加载会话
    manager.load_session()
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from infrastructure.logger import logger
from domain.exceptions import ConversationError


class ConversationManager:
    """
    会话管理器 - 单例模式
    
    属性:
        _instance: 类级别的单例实例
        _initialized: 标记是否已初始化
        history: 对话历史列表
        max_history: 最大历史消息数
        session_dir: 会话保存目录
        session_file: 当前会话文件路径
    
    设计说明:
        采用单例模式确保全局会话状态一致,
        避免多个实例导致的对话历史不同步。
    """
    
    _instance: Optional['ConversationManager'] = None
    
    def __new__(cls):
        """
        控制对象创建,实现单例模式
        
        返回:
            ConversationManager: 全局唯一的实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_history: int = 50):
        """
        初始化会话管理器
        
        参数:
            max_history: 最大历史消息数(默认50条)
        
        说明:
            使用_initialized标志避免重复初始化
        """
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        
        self.session_dir = Path.home() / '.macmind' / 'sessions'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_file = self.session_dir / 'default_session.json'
        
        logger.debug(f"ConversationManager初始化完成,最大历史: {max_history}")
    
    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史
        
        参数:
            role: 消息角色 ('user' | 'assistant' | 'system')
            content: 消息内容
        
        说明:
            - 自动维护历史消息数量上限
            - 添加时间戳用于调试和分析
        
        示例:
            manager.add_message("user", "帮我找一个绘图软件")
            manager.add_message("assistant", "我推荐drawio")
        """
        if not content or not content.strip():
            logger.warning("尝试添加空消息,已忽略")
            return
        
        message = {
            "role": role,
            "content": content.strip(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.history.append(message)
        
        if len(self.history) > self.max_history:
            removed = self.history.pop(0)
            logger.debug(f"历史消息达到上限,移除最早的消息: {removed['role']}")
        
        logger.debug(f"添加{role}消息,当前历史: {len(self.history)}条")
    
    def add_user_message(self, content: str):
        """
        添加用户消息
        
        参数:
            content: 用户消息内容
        
        示例:
            manager.add_user_message("帮我安装vim")
        """
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str):
        """
        添加AI助手响应
        
        参数:
            content: AI响应内容
        
        示例:
            manager.add_assistant_message("正在安装vim...")
        """
        self.add_message("assistant", content)
    
    def add_system_message(self, content: str):
        """
        添加系统消息
        
        参数:
            content: 系统消息内容
        
        说明:
            系统消息用于设置AI行为,通常放在对话开始
        
        示例:
            manager.add_system_message("你是一个Mac系统助手")
        """
        self.add_message("system", content)
    
    def get_context(self, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话上下文(用于AI调用)
        
        参数:
            max_messages: 最多返回的消息数(None=全部)
        
        返回:
            List[Dict]: 消息列表,每条消息包含role和content
        
        说明:
            - 返回格式符合OpenAI API要求
            - 移除timestamp字段(仅内部使用)
            - 可限制消息数量以控制token使用
            - 支持工具调用消息(tool_calls和tool角色)
        
        示例:
            context = manager.get_context(max_messages=10)
            response = ai_client.chat(messages=context)
        """
        messages = self.history if max_messages is None else self.history[-max_messages:]
        
        result = []
        for msg in messages:
            if msg["role"] == "tool":
                result.append({
                    "role": msg["role"],
                    "tool_call_id": msg["tool_call_id"],
                    "name": msg["name"],
                    "content": msg["content"]
                })
            elif "tool_calls" in msg:
                result.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "tool_calls": msg["tool_calls"]
                })
            else:
                result.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return result
    
    def get_last_messages(self, count: int = 5) -> List[Dict[str, str]]:
        """
        获取最近的N条消息
        
        参数:
            count: 消息数量
        
        返回:
            List[Dict]: 最近的消息列表
        
        示例:
            last_msgs = manager.get_last_messages(3)
        """
        return self.history[-count:] if self.history else []
    
    def clear_history(self):
        """
        清空对话历史
        
        使用场景:
            - 开始新对话
            - 重置上下文
            - 测试
        
        示例:
            manager.clear_history()
        """
        self.history.clear()
        logger.info("对话历史已清空")
    
    def get_message_count(self) -> int:
        """
        获取历史消息总数
        
        返回:
            int: 消息数量
        
        示例:
            count = manager.get_message_count()
        """
        return len(self.history)
    
    def get_conversation_turns(self) -> int:
        """
        获取对话轮次
        
        返回:
            int: 对话轮次(用户消息+AI响应=1轮)
        
        说明:
            轮次=用户消息数(假设每个用户消息都有AI响应)
        
        示例:
            turns = manager.get_conversation_turns()
        """
        return sum(1 for msg in self.history if msg["role"] == "user")
    
    def estimate_tokens(self) -> int:
        """
        估算当前会话的token数量
        
        返回:
            int: 估算的token数
        
        说明:
            使用简单规则估算: 1个中文字符≈1.5token, 1个英文单词≈1.3token
            实际token数可能有偏差,仅供参考
        
        示例:
            tokens = manager.estimate_tokens()
            if tokens > 4000:
                manager.clear_history()
        """
        total_tokens = 0
        
        for msg in self.history:
            content = msg["content"]
            
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            english_words = len(content.split())
            
            total_tokens += int(chinese_chars * 1.5 + english_words * 1.3)
        
        return total_tokens
    
    def save_session(self, session_name: str = "default") -> bool:
        """
        保存会话到文件
        
        参数:
            session_name: 会话名称(默认"default")
        
        返回:
            bool: 保存是否成功
        
        文件格式:
            JSON格式,包含历史消息和元数据
        
        示例:
            manager.save_session("my_session")
        """
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            session_data = {
                "name": session_name,
                "created_at": datetime.now().isoformat(),
                "message_count": len(self.history),
                "conversation_turns": self.get_conversation_turns(),
                "estimated_tokens": self.estimate_tokens(),
                "history": self.history
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"会话已保存: {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}", exc_info=True)
            raise ConversationError(
                "会话保存失败",
                session_name=session_name,
                cause=e
            )
    
    def load_session(self, session_name: str = "default") -> bool:
        """
        从文件加载会话
        
        参数:
            session_name: 会话名称(默认"default")
        
        返回:
            bool: 加载是否成功
        
        说明:
            - 加载会话会覆盖当前历史记录
            - 如果文件不存在,返回False不抛出异常
        
        示例:
            if manager.load_session("my_session"):
                print("会话加载成功")
        """
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            if not session_file.exists():
                logger.warning(f"会话文件不存在: {session_file}")
                return False
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.history = session_data.get("history", [])
            
            logger.info(
                f"会话已加载: {session_name}, "
                f"消息数: {len(self.history)}, "
                f"轮次: {self.get_conversation_turns()}"
            )
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"会话文件格式错误: {e}")
            raise ConversationError(
                "会话文件格式错误",
                session_name=session_name,
                cause=e
            )
        except Exception as e:
            logger.error(f"加载会话失败: {e}", exc_info=True)
            raise ConversationError(
                "会话加载失败",
                session_name=session_name,
                cause=e
            )
    
    def list_sessions(self) -> List[str]:
        """
        列出所有已保存的会话
        
        返回:
            List[str]: 会话名称列表
        
        示例:
            sessions = manager.list_sessions()
            for session in sessions:
                print(f"会话: {session}")
        """
        session_files = self.session_dir.glob("*_session.json")
        
        sessions = [
            f.stem.replace("_session", "")
            for f in session_files
        ]
        
        return sorted(sessions)
    
    def delete_session(self, session_name: str) -> bool:
        """
        删除已保存的会话
        
        参数:
            session_name: 会话名称
        
        返回:
            bool: 删除是否成功
        
        示例:
            manager.delete_session("old_session")
        """
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            if not session_file.exists():
                logger.warning(f"会话文件不存在: {session_file}")
                return False
            
            session_file.unlink()
            logger.info(f"会话已删除: {session_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除会话失败: {e}", exc_info=True)
            raise ConversationError(
                "会话删除失败",
                session_name=session_name,
                cause=e
            )
    
    def get_session_info(self, session_name: str) -> Optional[Dict]:
        """
        获取会话信息(不加载历史)
        
        参数:
            session_name: 会话名称
        
        返回:
            Dict: 会话元数据,不存在返回None
        
        示例:
            info = manager.get_session_info("my_session")
            if info:
                print(f"消息数: {info['message_count']}")
        """
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return {
                "name": session_data.get("name"),
                "created_at": session_data.get("created_at"),
                "message_count": session_data.get("message_count"),
                "conversation_turns": session_data.get("conversation_turns"),
                "estimated_tokens": session_data.get("estimated_tokens")
            }
            
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None
    
    def get_optimized_system_prompt(self) -> str:
        """
        获取优化后的系统提示词
        
        返回:
            str: 精心设计的系统提示词
        
        说明:
            这是经过优化的提示词工程,包含:
            - 明确的角色定位
            - 详细的能力描述
            - 交互指导
            - 最佳实践建议
        """
        prompt = """你是 MacMind 的 AI 助手,一个专业的 macOS 系统管理和软件管家。

你的能力范围:
1. 📦 软件管理
   - 搜索和推荐 macOS 软件
   - 分析软件许可证,优先推荐开源软件
   - 提供安装和卸载指导
   - 比较类似软件的优劣

2. 💻 系统控制
   - 控制 macOS 应用程序(打开、关闭、查询状态)
   - 管理系统通知设置
   - 帮助配置快捷键
   - 查询系统信息

3. ❓ 问题解答
   - 解释 macOS 系统功能
   - 提供故障排除建议
   - 分享最佳实践

交互原则:
- 💬 用友好、简洁的语言回答
- 🎯 精准理解用户意图,提供针对性建议
- 🛡️ 安全第一,在执行敏感操作前提醒用户
- 💡 主动提供相关建议和替代方案
- ✅ 确保推荐的软件具有清晰的许可证和合法性

回答格式:
- 使用适当的 emoji 提升可读性
- 重要信息用粗体标记
- 复杂步骤用编号列表
- 提供具体的命令示例

特别提醒:
- 当用户提到"绘图软件"、"视频编辑器"等,优先推荐免费开源软件
- 对于系统控制操作,说明所需权限和潜在风险
- 对于复杂配置,提供多种解决方案供用户选择

现在,请以专业、友好的方式帮助用户解决问题。"""
        return prompt.strip()
    
    def get_context_with_summary(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取带有上下文总结的对话历史
        
        参数:
            max_messages: 最多返回的消息数
        
        返回:
            List[Dict]: 消息列表,包含上下文总结
        
        说明:
            当对话历史较长时,生成一个简要总结放在前面,
            帮助 AI 更好地理解上下文。
        """
        messages = self.get_context(max_messages)
        
        if len(messages) <= 5:
            return messages
        
        turns = self.get_conversation_turns()
        topics = self._extract_topics(messages)
        
        summary = f"""对话上下文总结:
- 已进行 {turns} 轮对话
- 主要话题: {', '.join(topics)}
- 以下是最近的对话内容。"""
        
        context_with_summary = [
            {"role": "system", "content": summary}
        ] + (messages[-max_messages:] if max_messages else messages)
        
        return context_with_summary
    
    def _extract_topics(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        从消息中提取主题关键词
        
        参数:
            messages: 消息列表
        
        返回:
            List[str]: 主题关键词列表
        
        说明:
            使用简单的关键词匹配提取主题
        """
        topics = set()
        keywords = {
            "软件": ["搜索", "安装", "卸载", "软件", "应用"],
            "系统控制": ["打开", "关闭", "启动", "退出"],
            "通知管理": ["通知", "提醒", "消息"],
            "快捷键": ["快捷键", "短按键", "键盘"],
            "系统信息": ["版本", "信息", "状态"]
        }
        
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                for topic, words in keywords.items():
                    if any(word in content for word in words):
                        topics.add(topic)
        
        return list(topics) if topics else ["通用咨询"]
    
    def add_context_message(self, message: str):
        """
        添加上下文提示消息
        
        参数:
            message: 上下文提示内容
        
        说明:
            用于在对话中添加重要的上下文信息,
            帮助 AI 更好地理解当前状态。
        
        示例:
            manager.add_context_message("用户刚安装了 drawio")
        """
        self.add_system_message(f"[上下文] {message}")
    
    def add_tool_call_message(self, tool_calls: List[Dict[str, Any]]):
        """
        添加AI的工具调用消息
        
        参数:
            tool_calls: 工具调用列表,每个包含id, type, function等信息
        
        说明:
            当AI决定调用工具时,记录这些调用请求
        
        示例:
            manager.add_tool_call_message([
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search_software",
                        "arguments": '{"query": "vim"}'
                    }
                }
            ])
        """
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(message)
        logger.debug(f"添加工具调用消息,调用数: {len(tool_calls)}")
    
    def add_tool_result_message(self, tool_call_id: str, function_name: str, result: str):
        """
        添加工具执行结果消息
        
        参数:
            tool_call_id: 工具调用ID
            function_name: 函数名称
            result: 执行结果(JSON字符串)
        
        说明:
            将工具的执行结果反馈给AI
        
        示例:
            manager.add_tool_result_message(
                "call_123",
                "search_software",
                '{"success": true, "data": {...}}'
            )
        """
        message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": result,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(message)
        logger.debug(f"添加工具结果消息: {function_name}")
    
    def __repr__(self) -> str:
        """返回会话管理器的字符串表示"""
        return (
            f"ConversationManager("
            f"messages={len(self.history)}, "
            f"turns={self.get_conversation_turns()}, "
            f"tokens≈{self.estimate_tokens()})"
        )


conversation_manager = ConversationManager()
