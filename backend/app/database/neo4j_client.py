from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession


class Neo4jClient:
    _instance: Optional[Neo4jClient] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._driver: Optional[AsyncDriver] = None

    @classmethod
    async def get_instance(cls) -> Neo4jClient:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = Neo4jClient()
        return cls._instance

    async def connect(self, uri: str, user: str, password: str) -> None:
        self._driver = AsyncGraphDatabase.driver(
            uri, auth=(user, password), connection_timeout=5, max_transaction_retry_time=5
        )
        try:
            await self._driver.verify_connectivity()
        except Exception:
            pass

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver is not connected. Call connect() first.")
        return self._driver

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, db: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        driver = self._get_driver()
        async with driver.session(database=db or "neo4j") as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_read(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, db: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        driver = self._get_driver()

        async def _read_tx(tx, q, p):
            result = await tx.run(q, p)
            return await result.data()

        async with driver.session(database=db or "neo4j") as session:
            return await session.execute_read(lambda tx: _read_tx(tx, query, parameters or {}))

    async def execute_write(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, db: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        driver = self._get_driver()

        async def _write_tx(tx, q, p):
            result = await tx.run(q, p)
            return await result.data()

        async with driver.session(database=db or "neo4j") as session:
            return await session.execute_write(lambda tx: _write_tx(tx, query, parameters or {}))


async def get_neo4j() -> Neo4jClient:
    return await Neo4jClient.get_instance()
