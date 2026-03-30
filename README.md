# SCM Risk Intelligence Platform

A supply chain risk management platform for mega-project EPC companies. Uses a Neo4j knowledge graph to model relationships between projects, equipment, suppliers, shipping routes, and geopolitical risk zones, with AI-powered disruption analysis and mitigation recommendations.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Node.js 18+ (for frontend, when available)

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd icandothis

# 2. Run the setup script (starts Docker, waits for services, seeds the database)
bash scripts/setup.sh
```

This will:
1. Start Neo4j, PostgreSQL, and Redis via Docker Compose
2. Wait for all services to pass health checks
3. Seed the Neo4j graph database with sample supply chain data
4. Print connection URLs for all services

## Manual Setup

```bash
# Start infrastructure
docker compose up -d

# Wait for Neo4j to be ready, then seed
python backend/app/database/seed.py

# Start the backend API
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Service URLs

| Service | URL | Credentials |
|---|---|---|
| Backend API | http://localhost:8000 | - |
| Neo4j Browser | http://localhost:7474 | neo4j / scmrisk2024 |
| Neo4j Bolt | bolt://localhost:7687 | neo4j / scmrisk2024 |
| PostgreSQL | localhost:5432 | scmrisk / scmrisk2024 |
| Redis | localhost:6379 | - |

## Project Structure

```
backend/          Python FastAPI backend
  app/
    main.py       Application entry point
    config.py     Environment configuration
    database/     Neo4j and Redis clients, seed script
    models/       Pydantic domain models
    routers/      API route handlers
    services/     Business logic
    agents/       AI agent tools
data/
  seed/           JSON seed data for the knowledge graph
  scenarios/      Disruption scenario definitions
scripts/
  setup.sh        One-command local setup
docker-compose.yml
```

## Disruption Scenarios

Pre-built scenarios in `data/scenarios/` for testing and simulation:

- **Strait of Hormuz Blockade** - Severity 5, blocks 7 shipping routes
- **Suez Canal Obstruction** - Severity 4, affects 3 routes and 3 projects
- **Yokohama Earthquake** - Severity 4, impacts 3 Japanese suppliers
- **US-China Tariff Escalation** - Severity 3, 45% tariff on Chinese equipment
- **Expanded Russia Sanctions** - Severity 5, blocks Western exports to Russia

## Configuration

Copy `.env.example` to `.env` and set your values. See `backend/app/config.py` for all available settings and defaults.

## License

Proprietary. All rights reserved.
