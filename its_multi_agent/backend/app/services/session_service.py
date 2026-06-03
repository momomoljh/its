from json import JSONDecodeError
from typing import List, Any, Dict, Optional
from repositories.session_repository import session_repository
from infrastructure.logging.logger import logger


class SessionService:
    """
    会话业务服务类:

    负责处理会话和核心业务逻辑 包括:
    1. 对话流程编排(准备对话历史上下文、保存历史对话)
    2. 历史对话上下文窗口管理（保留最新5轮对话）
    3. 会话列表管理
    """

    # 默认会话id
    DEFAULT_SESSION_ID = "default"

    def __init__(self):
        """依赖注入会话数据仓储类"""
        self._repo = session_repository

    def prepare_history(self, user_id: str, session_id: str, user_input: str, max_rounds: int = 5) -> List[
        Dict[str, Any]]:
        """
        准备发送给LLM的上下文: 加载-->追加--->截断

        注意:此操作在内存中处理数据，不会保存到数据库(通常保存历对话)LLM回答之后

        Args:
            user_id: 用户id
            session_id: 会话id
            user_input: 当前问题
            max_rounds: 最大保留对话轮次

        Returns:
            List[Dict[str,Any]]
        """

        # 1. 加载现有历史
        chat_history = self.load_history(user_id, session_id)

        # 2. 追加用户当前输入
        chat_history.append({"role": "user", "content": user_input})

        # 3. 截断预留轮次
        final_history = self._truncate_history(chat_history, max_rounds)

        # 4. 返回
        return final_history

    def  load_history(self, user_id: str, session_id: Optional[str]) -> List[Dict[str, Any]]:
        """

        基于会话级别加载用户对话历史

        Args:
            user_id: 用户id
            session_id: 会话id

        Returns:
            List[Dict[str,Any]]: 有效的对话历史，如果历史对话对应的文件不存在，构建初始的对话上下文

        """
        try:
            # 1. 指定session_id
            target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID

            # 2. 尝试加载用户会话级别的历史对话文件
            history = self._repo.load_session(user_id, target_session_id)

            # 3. 初始化新会话
            if history is None:
                return self._init_new_session_history(target_session_id)

            # 4. 返回历史对话
            return history


        except JSONDecodeError as e:
            logger.error(f"用户 {user_id} 会话 {session_id} 记忆文件已损坏")
            return [{"role": "system", "content": "【系统提示】检测到记忆文件已损坏"}]

        except Exception as e:
            logger.error(f"加载会话异常:{e}")
            return []

    def save_history(self, user_id: str, session_id: str, chat_history: List[Dict[str, Any]]):
        """
         保存历史会话 通常在LLM回复之后调用
        Args:
            user_id:  用户id
            session_id:  会话id
            chat_history: 要保存的对话历史列表

        Returns:
        """

        # 1.判断要保存的历史对话
        if not chat_history:
            return
        target_session_id = session_id or self.DEFAULT_SESSION_ID
        # 2. 保存历史对话
        try:
            self._repo.save_session(user_id, target_session_id, chat_history)
        except Exception as e:
            logger.error(f"用户 {user_id} 会话 {session_id} 历史对话失败  {e}")

    def get_all_sessions_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取并格式化用户的所有会话列表（用于前端侧边栏展示）。

        Args:
            user_id: 用户唯一标识。

        Returns:
            List[Dict]: 按创建时间倒序排列的会话列表。
            格式示例:
            [
                {
                    "session_id": "...",
                    "create_time": "...",
                    "memory": [...],
                    "total_messages": 5
                }, ...
            ]
        """
        # 1. 从 Repo 获取原始元数据
        # 类型提示: List[Tuple[session_id, create_time, data_or_error]]
        raw_sessions = self._repo.get_all_sessions_metadata(user_id)

        formatted_sessions = []

        for session_id, create_time, data_or_error in raw_sessions:
            session_item = {
                "session_id": session_id,
                "create_time": create_time,
            }

            # 2. 处理可能的读取错误 (隔离异常，防止一个文件损坏导致整个列表挂掉)
            if isinstance(data_or_error, Exception):
                logger.error(
                    "读取会话 %s 失败: %s", session_id, str(data_or_error)
                )
                session_item.update({
                    "memory": [],
                    "total_messages": 0,
                    "error": "无法读取会话数据",
                })
            else:
                # 3. 正常数据处理：过滤 System 消息，只展示用户可见内容
                memory = data_or_error
                user_visible_memory = [
                    msg for msg in memory if msg.get("role") != "system"
                ]
                session_item.update({
                    "memory": user_visible_memory,
                    "total_messages": len(user_visible_memory),
                })

            formatted_sessions.append(session_item)

        # 4. 排序：按时间倒序（最新的在最前）
        formatted_sessions.sort(
            key=lambda x: x.get("create_time") or "",
            reverse=True
        )

        return formatted_sessions

    def _init_new_session_history(self, target_session_id: str) -> List[Dict[str, Any]]:
        """
        创建新会话的历史对话
        Args:
            target_session_id: 用户id

        Returns:
         List[Dict[str,Any]]

        """

        return [
            {
                "role": "system",
                "content": f"你是一个有记忆的智能体助手，请基于上下文历史会话用户问题 会话ID( {target_session_id} )"

            }
        ]

    def _truncate_history(self, chat_history: List[Dict[str, Any]], max_rounds: int):
        """
         截断记忆: 保留system_message+最新N轮对话

        Args:
            chat_history: 加载+拼接的历史会话
            max_rounds: 最大保留轮数

        Returns:
            List[Dict[str,Any]]: 最终发送给LLM的历史对话

        """

        # 1. 提取System消息（无条件留）
        system_msg = [msg for msg in chat_history if msg.get('role') == 'system']

        # 2. 提取非System消息(User & AI)
        no_system_msg = [msg for msg in chat_history if msg.get('role') != 'system']

        # 3. 截取
        limit = 2 * max_rounds
        truncate_msgs = no_system_msg[-limit:]

        # 4. 返回（重新组合）
        return system_msg + truncate_msgs


session_service = SessionService()