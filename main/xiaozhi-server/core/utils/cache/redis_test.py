
import time
import pickle
import json
from typing import Any, Optional, Dict, Callable, List
from enum import Enum
import redis
from redis.exceptions import RedisError

from core.utils.cache.config import CacheType
from core.utils.cache.redis_manager import GlobalCacheManager

if __name__ == '__main__':
    redis_config = {
        "host": "10.16.32.3",
        "port": 6379,
        "db": 0,
        # "password": "your_redis_password",
    }
    cache_manager = GlobalCacheManager(redis_config)
    cache_manager.set(CacheType.CONFIG, "user_1001", {"name": "张三", "age": 25})
    # 设置缓存
    cache_manager.set(CacheType.CONFIG, "user_1001", {"name": "张三", "age": 25}, ttl=3600)

    # 获取缓存
    user = cache_manager.get(CacheType.CONFIG, "user_1001")
    print(user)  # {'name': '张三', 'age': 25}

    # 批量设置
    cache_manager.batch_set(CacheType.CONFIG, {
        "prod_1001": {"name": "手机", "price": 2999},
        "prod_1002": {"name": "电脑", "price": 5999}
    }, ttl=1800)

    # 按模式删除
    deleted = cache_manager.invalidate_pattern(CacheType.CONFIG, "prod_100")
    print(f"删除 {deleted} 个产品缓存")

    # 清空缓存
    cache_manager.clear(CacheType.CONFIG)

    # 查看统计
    stats = cache_manager.get_stats()
    print(f"缓存命中率: {stats['hit_ratio']:.2%}")