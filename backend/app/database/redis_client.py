from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import redis.asyncio as aioredis


class RedisClient:
    _instance: Optional[RedisClient] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    @classmethod
    async def get_instance(cls) -> RedisClient:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = RedisClient()
        return cls._instance

    async def connect(self, url: str) -> None:
        self._client = aioredis.from_url(url, decode_responses=True)
        await self._client.ping()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        return await client.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        client = self._get_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)

    async def publish(self, channel: str, message: Any) -> None:
        client = self._get_client()
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        await client.publish(channel, message)

    async def subscribe(self, channel: str):
        client = self._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


async def get_redis() -> RedisClient:
    return await RedisClient.get_instance()
