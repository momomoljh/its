import json
import os.path
from datetime import datetime
from os.path import exists
from typing import Dict, List, Tuple, Any, Optional

from infrastructure.logging.logger import logger


class SessionRepository(object):
    """会话数据仓储类。

       负责处理底层的会话文件存储、读取和文件系统操作。
       """

    def __init__(self):
        """初始化 SessionRepository。

        自动设定存储目录。假设当前文件位于 backend/app/repository/。
        """
        # 获取项目根目录 (backend/app)
        # 假设层级为: backend/app/repository/session_repository.py

        self._base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self._memory_dir = os.path.join(self._base_dir, 'user_memories')

        if not os.path.exists(self._memory_dir):
            os.makedirs(self._memory_dir)

    def _get_user_directory(self, user_id: str) -> str:
        """获取用户的记忆文件夹路径。

        Args:
            user_id: 用户的唯一标识符。

        Returns:
            用户目录的绝对路径。
        """
        user_dir = os.path.join(self._memory_dir, user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir

    def _get_file_path(self, user_id: str, session_id: str) -> str:
        """获取具体会话文件的路径。"""
        user_dir = self._get_user_directory(user_id)
        return os.path.join(user_dir, f"{session_id}.json")

    def load_session(self, user_id: str, session_id: str) -> Optional[List[Dict]]:
        """从文件加载会话数据。

        Args:
            user_id: 用户ID。
            session_id: 会话ID。

        Returns:
            如果文件存在且解析成功，返回列表数据；如果文件不存在，返回 None。

        Raises:
            json.JSONDecodeError: 如果文件内容损坏无法解析。
        """
        file_path = self._get_file_path(user_id, session_id)

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_session(
            self, user_id: str, session_id: str, data: List[Dict]
    ) -> None:
        """保存会话数据到文件。

        Args:
            user_id: 用户ID。
            session_id: 会话ID。
            data: 要保存的数据列表。
        """
        file_path = self._get_file_path(user_id, session_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_sessions_metadata(
            self, user_id: str
    ) -> List[Tuple[str, str, Any]]:
        """获取用户所有会话的元数据和内容。

        Args:
            user_id: 用户ID。

        Returns:
            一个列表，包含元组 (session_id, create_time_str, raw_data_or_error)。
            raw_data_or_error 可能是解析后的数据 list，也可能是 Exception 对象。
        """
        user_dir = self._get_user_directory(user_id)
        results = []

        try:
            for filename in os.listdir(user_dir):
                if not filename.endswith(".json"):
                    continue

                session_id = filename[:-5]
                file_path = os.path.join(user_dir, filename)

                # 获取创建时间
                timestamp = os.path.getctime(file_path)
                create_time = datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # 尝试读取内容
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    results.append((session_id, create_time, data))
                except Exception as e:
                    # 如果读取失败，将错误对象传回，交给 Service 处理
                    results.append((session_id, create_time, e))

        except FileNotFoundError:
            logger.warning(f"用户目录不存在: {user_id}")
            return []
        except Exception as e:
            logger.error(f"遍历用户会话目录出错: {str(e)}")
            return []

        return results

# 全局单例
session_repository = SessionRepository()