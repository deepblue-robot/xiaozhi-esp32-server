# core/chat_cache/chat_cache_manager.py
import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import redis
from loguru import logger
# from core.utils.cache.redis_manager  import GlobalCacheManager
TAG = __name__


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChatMessage':
        return cls(**data)

    def to_llm_format(self) -> dict:
        """转换为 LLM 所需格式"""
        return {"role": self.role, "content": self.content}


@dataclass
class SessionInfo:
    """会话信息"""
    device_id: str
    session_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    client_ip: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SessionInfo':
        return cls(**data)


class ChatCacheManager:
    """
    聊天缓存管理器
    - 实时缓存聊天消息到 Redis
    - 支持会话恢复
    - 自动过期清理
    """

    def __init__(
            self,
            redis_client: redis.Redis,
            # redis_config: dict = None,
            key_prefix: str = "chat:cache",
            default_ttl: int = 86400,  # 默认 24 小时过期
            max_messages: int = 100,  # 每个会话最大消息数
    ):
        """
        Args:
            redis_client: Redis 客户端实例
            redis_config: Redis 配置（如果没有传入 client）
            key_prefix: Redis key 前缀
            default_ttl: 缓存过期时间（秒）
            max_messages: 每个会话保留的最大消息数
        """
        if redis_client:
            self.redis = redis_client
        # elif redis_config:
        #     self.redis = redis.Redis(**redis_config, decode_responses=True)
        else:
            raise ValueError("必须提供 redis_client 或 redis_config")

        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.max_messages = max_messages

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Key 生成方法
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _messages_key(self, device_id: str) -> str:
        """消息列表 key"""
        return f"{self.key_prefix}:messages:{device_id}"

    def _session_key(self, device_id: str) -> str:
        """会话信息 key"""
        return f"{self.key_prefix}:session:{device_id}"

    def _device_index_key(self) -> str:
        """设备索引 key（用于管理所有活跃设备）"""
        return f"{self.key_prefix}:devices"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 会话管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start_session(
            self,
            device_id: str,
            session_id: str,
            user_id: Optional[str] = None,
            client_ip: Optional[str] = None,
            metadata: Optional[dict] = None,
            restore_previous: bool = True,
    ) -> tuple[SessionInfo, List[ChatMessage]]:
        """
        开始会话

        Args:
            device_id: 设备 ID
            session_id: 当前会话 ID
            user_id: 用户 ID
            client_ip: 客户端 IP
            metadata: 额外元数据
            restore_previous: 是否恢复之前的对话

        Returns:
            (session_info, previous_messages): 会话信息和历史消息
        """
        previous_messages = []

        # 检查是否有之前的会话
        if restore_previous:
            previous_messages = self.get_messages(device_id)
            if previous_messages:
                logger.bind(tag=TAG).info(
                    f"恢复设备 {device_id} 的历史会话，共 {len(previous_messages)} 条消息"
                )

        # 创建/更新会话信息
        session_info = SessionInfo(
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            client_ip=client_ip,
            metadata=metadata or {},
        )

        # 保存会话信息
        self._save_session_info(session_info)

        # 添加到设备索引
        self.redis.sadd(self._device_index_key(), device_id)

        return session_info, previous_messages

    def end_session(self, device_id: str, clear_cache: bool = False):
        """
        结束会话

        Args:
            device_id: 设备 ID
            clear_cache: 是否清除缓存（默认保留，以便恢复）
        """
        if clear_cache:
            self.clear_cache(device_id)
        else:
            # 更新会话结束时间
            session_info = self.get_session_info(device_id)
            if session_info:
                session_info.updated_at = time.time()
                self._save_session_info(session_info)

        logger.bind(tag=TAG).debug(f"会话结束: device_id={device_id}, clear={clear_cache}")

    def _save_session_info(self, session_info: SessionInfo):
        """保存会话信息"""
        key = self._session_key(session_info.device_id)
        self.redis.set(
            key,
            json.dumps(session_info.to_dict(), ensure_ascii=False),
            ex=self.default_ttl
        )

    def get_session_info(self, device_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        key = self._session_key(device_id)
        data = self.redis.get(key)
        if data:
            return SessionInfo.from_dict(json.loads(data))
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 消息管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_message(
            self,
            device_id: str,
            role: str,
            content: str,
            message_id: Optional[str] = None,
            metadata: Optional[dict] = None,
    ) -> ChatMessage:
        """
        添加消息到缓存

        Args:
            device_id: 设备 ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            message_id: 消息 ID
            metadata: 额外元数据

        Returns:
            添加的消息对象
        """
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            message_id=message_id,
            metadata=metadata or {},
        )

        key = self._messages_key(device_id)

        # 使用 pipeline 保证原子性
        pipe = self.redis.pipeline()

        # 添加消息到列表末尾
        pipe.rpush(key, json.dumps(message.to_dict(), ensure_ascii=False))

        # 保留最近的 N 条消息
        pipe.ltrim(key, -self.max_messages, -1)

        # 更新过期时间
        pipe.expire(key, self.default_ttl)

        pipe.execute()

        logger.bind(tag=TAG).debug(
            f"添加消息: device_id={device_id}, role={role}, content_len={len(content)}"
        )

        return message

    def add_user_message(
            self,
            device_id: str,
            content: str,
            **kwargs
    ) -> ChatMessage:
        """添加用户消息"""
        return self.add_message(device_id, MessageRole.USER.value, content, **kwargs)

    def add_assistant_message(
            self,
            device_id: str,
            content: str,
            **kwargs
    ) -> ChatMessage:
        """添加助手消息"""
        return self.add_message(device_id, MessageRole.ASSISTANT.value, content, **kwargs)

    def add_system_message(
            self,
            device_id: str,
            content: str,
            **kwargs
    ) -> ChatMessage:
        """添加系统消息"""
        return self.add_message(device_id, MessageRole.SYSTEM.value, content, **kwargs)

    def get_messages(
            self,
            device_id: str,
            limit: Optional[int] = None,
            include_system: bool = True,
    ) -> List[ChatMessage]:
        """
        获取缓存的消息

        Args:
            device_id: 设备 ID
            limit: 返回消息数量限制（None 表示全部）
            include_system: 是否包含系统消息

        Returns:
            消息列表
        """
        key = self._messages_key(device_id)

        if limit:
            # 获取最近 N 条
            data_list = self.redis.lrange(key, -limit, -1)
        else:
            # 获取全部
            data_list = self.redis.lrange(key, 0, -1)

        messages = []
        for data in data_list:
            try:
                msg = ChatMessage.from_dict(json.loads(data))
                if include_system or msg.role != MessageRole.SYSTEM.value:
                    messages.append(msg)
            except Exception as e:
                logger.bind(tag=TAG).warning(f"解析消息失败: {e}")

        return messages

    def get_messages_for_llm(
            self,
            device_id: str,
            limit: Optional[int] = None,
            include_system: bool = False,
    ) -> List[dict]:
        """
        获取 LLM 格式的消息列表

        Returns:
            [{"role": "user", "content": "..."}, ...]
        """
        messages = self.get_messages(device_id, limit, include_system)
        return [msg.to_llm_format() for msg in messages]

    def get_message_count(self, device_id: str) -> int:
        """获取消息数量"""
        key = self._messages_key(device_id)
        return self.redis.llen(key)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 缓存管理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def clear_cache(self, device_id: str):
        """清除设备的所有缓存"""
        pipe = self.redis.pipeline()
        pipe.delete(self._messages_key(device_id))
        pipe.delete(self._session_key(device_id))
        pipe.srem(self._device_index_key(), device_id)
        pipe.execute()

        logger.bind(tag=TAG).info(f"已清除设备缓存: {device_id}")

    def refresh_ttl(self, device_id: str, ttl: Optional[int] = None):
        """刷新缓存过期时间"""
        ttl = ttl or self.default_ttl
        pipe = self.redis.pipeline()
        pipe.expire(self._messages_key(device_id), ttl)
        pipe.expire(self._session_key(device_id), ttl)
        pipe.execute()

    def has_cache(self, device_id: str) -> bool:
        """检查设备是否有缓存"""
        return self.redis.exists(self._messages_key(device_id)) > 0

    def get_active_devices(self) -> List[str]:
        """获取所有活跃设备"""
        return list(self.redis.smembers(self._device_index_key()))

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        devices = self.get_active_devices()
        total_messages = 0

        for device_id in devices:
            total_messages += self.get_message_count(device_id)

        return {
            "active_devices": len(devices),
            "total_messages": total_messages,
            "max_messages_per_device": self.max_messages,
            "default_ttl": self.default_ttl,
        }