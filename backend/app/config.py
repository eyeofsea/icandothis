from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "scmrisk2024"

    # PostgreSQL
    POSTGRES_URL: str = "postgresql+asyncpg://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"
    SQLALCHEMY_DATABASE_URL: str = "postgresql+asyncpg://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"
    SQLALCHEMY_SYNC_URL: str = "postgresql://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # App
    APP_NAME: str = "SCM Risk Intelligence Platform"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
