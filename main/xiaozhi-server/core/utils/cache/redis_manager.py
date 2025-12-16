"""
Redis 版全局缓存管理器（兼容原接口）
"""
import time
import pickle
import json
from typing import Any, Optional, Dict, Callable, List
from enum import Enum
import redis
from redis.exceptions import RedisError

from .config import CacheConfig, CacheType




class CacheStrategy(Enum):
    LRU = "lru"
    TTL_LRU = "ttl_lru"
    FIFO = "fifo"

class GlobalCacheManager:
    """Redis 实现的全局缓存管理器（兼容原接口）"""

    def __init__(self, redis_config: Dict[str, Any] = None):
        # Redis 连接配置（默认本地）
        default_redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "decode_responses": False,  # 保持字节流，手动序列化
            "socket_timeout": 5,
            "retry_on_timeout": True
        }
        self.redis_config = redis_config or default_redis_config
        self._redis_client = None
        self._logger = None
        # 统计信息（内存中维护，如需持久化可存入 Redis）
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "cleanups": 0}

    @property
    def redis_client(self) -> redis.Redis:
        """懒加载 Redis 客户端"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(**self.redis_config)
                # 测试连接
                self._redis_client.ping()
            except RedisError as e:
                raise RuntimeError(f"Redis 连接失败: {e}") from e
        return self._redis_client

    @property
    def logger(self):
        """延迟初始化 logger 以避免循环导入"""
        if self._logger is None:
            from config.logger import setup_logging
            self._logger = setup_logging()
        return self._logger

    def _serialize(self, value: Any) -> bytes:
        """序列化 Python 对象"""
        try:
            # 优先尝试 JSON 序列化（更通用）
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError):
            # 复杂对象用 pickle
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """反序列化 Redis 数据"""
        if not data:
            return None
        try:
            # 先尝试 JSON
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 再尝试 pickle
            return pickle.loads(data)

    def _get_redis_key(self, cache_type: CacheType, key: str, namespace: str = "") -> str:
        """生成 Redis Key（带命名空间）"""
        parts = [cache_type.value]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return ":".join(parts)

    def set(
            self,
            cache_type: CacheType,
            key: str,
            value: Any,
            ttl: Optional[float] = None,
            namespace: str = "",
    ) -> None:
        """设置缓存（Redis 版）"""
        redis_key = self._get_redis_key(cache_type, key, namespace)
        config = CacheConfig.for_type(cache_type)
        effective_ttl = ttl if ttl is not None else config.ttl

        try:
            # 序列化值
            serialized_value = self._serialize(value)

            # 设置缓存 + TTL
            if effective_ttl is not None and effective_ttl> 0:
                # Redis EX 单位为秒，支持浮点型（自动转毫秒）
                self.redis_client.setex(
                    name=redis_key,
                    time=effective_ttl,
                    value=serialized_value
                )
            else:
                self.redis_client.set(redis_key, serialized_value)

            self.logger.info(f"Redis 设置缓存成功 key={redis_key}, ttl={effective_ttl}")
            # Redis 自带 LRU 淘汰（需配置 maxmemory-policy）
            # 如需手动控制大小，可在此处检查并删除旧键（可选）
            self._check_and_evict(cache_type, namespace, config.max_size)

        except RedisError as e:
            self.logger.error(f"Redis 设置缓存失败 key={redis_key}: {e}")
            raise

    def get(
            self, cache_type: CacheType, key: str, namespace: str = ""
    ) -> Optional[Any]:
        """获取缓存（Redis 版）"""
        redis_key = self._get_redis_key(cache_type, key, namespace)

        try:
            # 获取数据
            data = self.redis_client.get(redis_key)

            if data is None:
                self._stats["misses"] += 1
                return None

            # 反序列化
            value = self._deserialize(data)
            self._stats["hits"] += 1

            # LRU 策略：更新访问时间（Redis GET 自动更新 LRU 访问时间）
            return value

        except RedisError as e:
            self.logger.error(f"Redis 获取缓存失败 key={redis_key}: {e}")
            self._stats["misses"] += 1
            return None

    def delete(self, cache_type: CacheType, key: str, namespace: str = "") -> bool:
        """删除缓存"""
        redis_key = self._get_redis_key(cache_type, key, namespace)
        try:
            result = self.redis_client.delete(redis_key)
            return result > 0
        except RedisError as e:
            self.logger.error(f"Redis 删除缓存失败 key={redis_key}: {e}")
            return False

    def clear(self, cache_type: CacheType, namespace: str = "") -> None:
        """清空指定缓存（按前缀删除）"""
        # 构造匹配前缀
        prefix = self._get_redis_key(cache_type, "*", namespace).rstrip("*")
        try:
            # 批量删除（非原子操作，生产环境建议用 SCAN 避免阻塞）
            keys = self.redis_client.keys(f"{prefix}*")
            if keys:
                self.redis_client.delete(*keys)
        except RedisError as e:
            self.logger.error(f"Redis 清空缓存失败 prefix={prefix}: {e}")
            raise

    def invalidate_pattern(
            self, cache_type: CacheType, pattern: str, namespace: str = ""
    ) -> int:
        """按模式失效缓存"""
        prefix = self._get_redis_key(cache_type, "", namespace)
        search_pattern = f"{prefix}:*{pattern}*" if prefix else f"*{pattern}*"

        try:
            # 使用 SCAN 迭代，避免 KEYS 阻塞
            deleted_count = 0
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=search_pattern, count=100)
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            return deleted_count
        except RedisError as e:
            self.logger.error(f"Redis 按模式失效缓存失败 pattern={search_pattern}: {e}")
            return 0

    def _check_and_evict(self, cache_type: CacheType, namespace: str, max_size: int):
        """检查并淘汰超出大小限制的缓存（可选）"""
        if max_size <= 0:
            return

        prefix = self._get_redis_key(cache_type, "*", namespace).rstrip("*")
        # 统计当前前缀下的键数量
        cursor = 0
        key_count = 0
        while True:
            cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
            key_count += len(keys)
            if cursor == 0:
                break

        # 超出限制时淘汰最旧的键（按创建时间/过期时间）
        if key_count > max_size:
            excess = key_count - max_size
            # 获取所有键并按过期时间排序（Redis 2.8+ 支持 EXPIRETIME）
            cursor = 0
            keys_with_ttl = []
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
                for key in keys:
                    try:
                        # 获取过期时间（-1 表示永不过期）
                        ttl = self.redis_client.expiretime(key)
                        keys_with_ttl.append((key, ttl))
                    except RedisError:
                        continue
                if cursor == 0:
                    break

            # 按过期时间升序排序（先过期的先淘汰）
            keys_with_ttl.sort(key=lambda x: x[1] if x[1] != -1 else float("inf"))
            # 淘汰超出的键
            for key, _ in keys_with_ttl[:excess]:
                self.redis_client.delete(key)
                self._stats["evictions"] += 1

    def batch_set(
            self,
            cache_type: CacheType,
            items: Dict[str, Any],
            ttl: Optional[float] = None,
            namespace: str = ""
    ) -> None:
        """批量设置缓存（Redis Pipeline 优化）"""
        config = CacheConfig.for_type(cache_type)
        effective_ttl = ttl if ttl is not None else config.ttl

        try:
            # 使用 Pipeline 批量操作
            pipe = self.redis_client.pipeline()
            for key, value in items.items():
                redis_key = self._get_redis_key(cache_type, key, namespace)
                serialized_value = self._serialize(value)
                if effective_ttl is not None and effective_ttl > 0:
                    pipe.setex(redis_key, effective_ttl, serialized_value)
                else:
                    pipe.set(redis_key, serialized_value)
            pipe.execute()

            self._check_and_evict(cache_type, namespace, config.max_size)
        except RedisError as e:
            self.logger.error(f"Redis 批量设置缓存失败: {e}")
            raise

    def preload(
            self,
            cache_type: CacheType,
            loader_func: Callable[[str], Any],
            keys: List[str],
            ttl: Optional[float] = None,
            namespace: str = ""
    ) -> None:
        """缓存预热"""
        items = {}
        for key in keys:
            try:
                items[key] = loader_func(key)
            except Exception as e:
                self.logger.error(f"预加载缓存 key={key} 失败: {e}")

        if items:
            self.batch_set(cache_type, items, ttl, namespace)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_keys = 0
        # 统计 Redis 中所有缓存键数量（可选）
        try:
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, count=1000)
                total_keys += len(keys)
                if cursor == 0:
                    break
        except RedisError:
            total_keys = -1

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_ratio": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
            if (self._stats["hits"] + self._stats["misses"]) > 0 else 0.0,
            "total_keys_in_redis": total_keys
        }


# 全局实例
cache_manager = GlobalCacheManager(
    redis_config={
        "host": "10.16.32.3",
        "port": 6379,
        "db": 0,
        # "password": "your_redis_password",
    }
)