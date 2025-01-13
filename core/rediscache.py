#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'zfanswer'
import time
import redis
import os


class RedisCache:
    def __init__(self, expiry_time=60, app_id=None):
        #self.expiry_time = expiry_time
        self.expiry_time = -1 # 设置永不过期
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD", "")
        db = int(os.getenv("REDIS_DB", "0"))
        self.redis_client = redis.Redis(host=host, port=port, db=db, password=password)
        self.app_name = os.getenv("APP_NAME", "dify-on-dingtalk")
        if app_id:
            self.app_name = f"{self.app_name}:{app_id}"

    def _is_expired(self, key):
        # 使用原始的key检查是否过期
        # 如果 expiry_time 为 -1，表示永不过期
        if self.expiry_time == -1:
            return False
        # 检查键是否过期
        ttl = self.redis_client.ttl(key)
        if ttl == -2:  # 键不存在
            return True
        if ttl == -1:  # 键存在但没有设置过期时间
            return False
        return ttl <= 0  # 键已过期

    def set(self, key, value):
        # 对操作的key添加前缀
        key = f"{self.app_name}:{key}"
        if self.expiry_time == -1:
            # 永不过期，使用 set 方法
            self.redis_client.set(key, value)
        else:
            # 设置过期时间，使用 setex 方法
            self.redis_client.setex(key, self.expiry_time, value)

    def get(self, key):
        # 对操作的key添加前缀
        key = f"{self.app_name}:{key}"
        if self.redis_client.exists(key):
            if not self._is_expired(key):
                value = self.redis_client.get(key)
                return value.decode('utf-8')  # Redis 返回的是字节串，需要解码为字符串
            else:
                self.redis_client.delete(key)  # 如果过期，删除该键
        return None

    def cleanup(self):
        # 如果 expiry_time 为 -1，不需要清理
        if self.expiry_time == -1:
            return
        # 清理过期的键
        # 获取所有以 app_name 开头的键,本身带有前缀
        keys = self.redis_client.keys(f'{self.app_name}:*')
        for key in keys:
            # 如果键已过期，删除它
            if self._is_expired(key):
                self.redis_client.delete(key)

    def __str__(self):
        # 用于查看缓存内容
        keys = self.redis_client.keys(f'{self.app_name}:*')
        cache = {}
        for key in keys:
            if not self._is_expired(key):
                value = self.redis_client.get(key)
                cache[key.decode('utf-8')] = value.decode('utf-8')
        return str(cache)


if __name__ == "__main__":
    # 使用示例
    cache = RedisCache(expiry_time=-1)  # 设置永不过期

    cache.set("a", "1")
    cache.set("b", "2")

    time.sleep(3)
    print(cache.get("a"))  # 输出: 1

    time.sleep(3)
    print(cache.get("a"))  # 输出: 1, 因为永不过期