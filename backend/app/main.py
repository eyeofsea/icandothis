import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.neo4j_client import Neo4jClient
from app.database.redis_client import RedisClient

logger = logging.getLogger(__name__)
from app.routers import (
    analytics,
    chat,
    disruptions,
    equipment,
    hedging,
    ontology,
    projects,
    routes,
    suppliers,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    neo4j = await Neo4jClient.get_instance()
    await neo4j.connect(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)

    redis = await RedisClient.get_instance()
    await redis.connect(settings.REDIS_URL)

    try:
        from app.database.sync_pg import sync_all
        sync_result = await sync_all()
        logger.info(f"PostgreSQL sync complete: {sync_result}")
    except Exception as e:
        logger.warning(f"PostgreSQL sync skipped: {e}")

    yield

    await neo4j.close()
    await redis.close()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(equipment.router)
app.include_router(suppliers.router)
app.include_router(routes.router)
app.include_router(disruptions.router)
app.include_router(ontology.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(hedging.router)


@app.get("/health")
async def health_check():
    neo4j = await Neo4jClient.get_instance()
    redis = await RedisClient.get_instance()

    neo4j_ok = False
    redis_ok = False

    try:
        await neo4j.execute_query("RETURN 1 AS ok")
        neo4j_ok = True
    except Exception:
        pass

    try:
        await redis.get("__health")
        redis_ok = True
    except Exception:
        pass

    status = "healthy" if (neo4j_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "services": {
            "neo4j": "connected" if neo4j_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        pass
