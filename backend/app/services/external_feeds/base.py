"""Base class for external data feed integrations."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ExternalFeed(ABC):
    """Base class for all external data feeds."""

    def __init__(self, api_key: Optional[str] = None, cache_ttl_minutes: int = 60):
        self.api_key = api_key
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get(self, cache_key: str, **kwargs: Any) -> Any:
        if cache_key in self._cache:
            cached_at, data = self._cache[cache_key]
            if datetime.utcnow() - cached_at < self.cache_ttl:
                return data

        try:
            data = await self.fetch(**kwargs)
            self._cache[cache_key] = (datetime.utcnow(), data)
            return data
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} fetch failed: {e}")
            if cache_key in self._cache:
                return self._cache[cache_key][1]  # stale cache
            return self.fallback(**kwargs)

    @abstractmethod
    async def fetch(self, **kwargs: Any) -> Any:
        pass

    def fallback(self, **kwargs: Any) -> Any:
        return {}

    async def close(self) -> None:
        await self._client.aclose()
