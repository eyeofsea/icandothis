# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

SCM Risk Intelligence Platform - a supply chain risk management system for mega-project EPC (Engineering, Procurement, Construction) companies. It uses a Neo4j knowledge graph to model the relationships between projects, equipment, suppliers, shipping routes, ports, and geopolitical zones, then applies AI-driven analysis to assess disruption impacts and recommend mitigations.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / Uvicorn
- **Graph Database**: Neo4j 5.17 (Bolt protocol on port 7687, browser on 7474)
- **Relational DB**: PostgreSQL 16 (port 5432)
- **Cache**: Redis 7 (port 6379)
- **AI**: Anthropic Claude API via `anthropic` and `langchain-anthropic` SDKs
- **Frontend**: (planned) React/Next.js or similar
- **Infrastructure**: Docker Compose for local development

## Repository Structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database/
│   │   │   ├── neo4j_client.py  # Async Neo4j driver singleton
│   │   │   ├── redis_client.py  # Async Redis client singleton
│   │   │   └── seed.py          # Database seeding script
│   │   ├── models/              # Pydantic models (domain types)
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── services/            # Business logic layer
│   │   ├── agents/              # AI agent tools and orchestration
│   │   └── websocket/           # WebSocket handlers
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── seed/                    # JSON seed data for Neo4j
│   │   └── projects.json
│   └── scenarios/               # Disruption scenario definitions
│       ├── hormuz_blockade.json
│       ├── suez_obstruction.json
│       ├── japan_earthquake.json
│       ├── china_tariff.json
│       └── russia_sanctions.json
├── scripts/
│   └── setup.sh                 # Full local setup script
├── docker-compose.yml           # Neo4j, PostgreSQL, Redis
└── CLAUDE.md                    # This file
```

## Key Concepts / Domain Model

The Neo4j graph has these node types and relationships:

**Nodes:**
- `Project` (projectId) - EPC mega-projects (oil refineries, petrochemical plants, etc.)
- `Equipment` (equipmentId) - Individual pieces of equipment being procured
- `Supplier` (supplierId) - Equipment manufacturers/vendors
- `PurchaseOrder` (poId) - Procurement orders linking equipment to suppliers
- `ShippingRoute` (routeId) - Maritime/land shipping routes
- `Port` (portId) - Departure and arrival ports
- `GeopoliticalZone` (zoneId) - Risk zones (straits, canals, conflict areas)

**Relationships:**
- `(Project)-[:HAS_EQUIPMENT]->(Equipment)`
- `(Equipment)-[:ORDERED_VIA]->(PurchaseOrder)`
- `(PurchaseOrder)-[:ISSUED_TO]->(Supplier)`
- `(Equipment)-[:SUPPLIED_BY]->(Supplier)`
- `(Equipment)-[:SHIPPED_VIA]->(ShippingRoute)`
- `(ShippingRoute)-[:PASSES_THROUGH]->(GeopoliticalZone)`
- `(ShippingRoute)-[:DEPARTS_FROM]->(Port)`
- `(ShippingRoute)-[:ARRIVES_AT]->(Port)`
- `(Supplier)-[:LOCATED_NEAR]->(Port)`
- `(Supplier)-[:HAS_ALTERNATIVE]->(Supplier)`
- `(ShippingRoute)-[:HAS_ALTERNATIVE]->(ShippingRoute)`
- `(Equipment)-[:HAS_SUBSTITUTE]->(Equipment)`

## Common Commands

```bash
# Start all infrastructure services
docker compose up -d

# Full setup (Docker + seed)
bash scripts/setup.sh

# Run backend API
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Seed Neo4j database
python backend/app/database/seed.py

# Run as module
python -m backend.app.database.seed
```

## Environment Variables

All configured via `.env` file or environment. See `backend/app/config.py` for defaults:

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `scmrisk2024` | Neo4j password |
| `POSTGRES_URL` | `postgresql+asyncpg://scmrisk:scmrisk2024@localhost:5432/scm_risk_db` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `ANTHROPIC_API_KEY` | (empty) | Anthropic API key for Claude |

## Neo4j Credentials

- **Browser**: http://localhost:7474
- **Bolt**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: scmrisk2024

## Coding Conventions

- Python code follows PEP 8 with type annotations throughout.
- Use `async`/`await` for all database and HTTP operations in the FastAPI app.
- The seed script uses synchronous Neo4j driver (not async) for simplicity.
- Pydantic models live in `backend/app/models/` and are used for request/response validation.
- All Neo4j queries should use parameterized queries (never string interpolation).
- Batch operations via `UNWIND` for bulk inserts.
- JSON files with nested structures are serialized to strings before storing as Neo4j properties.

## Disruption Scenarios

The `data/scenarios/` directory contains pre-defined disruption scenarios used for simulation and testing. Each scenario defines an event, its impacts on the supply chain graph, and recommended mitigations. Scenarios are loaded on-demand by the disruption analysis service, not during seed.

## Testing

Run tests from the project root:

```bash
pytest backend/ -v
```

## Important Notes

- The seed script clears all existing data before re-seeding (`MATCH (n) DETACH DELETE n`).
- Seed data files must be placed in `data/seed/` as JSON arrays (one file per node type).
- The async Neo4j client in `neo4j_client.py` is a singleton; always access via `Neo4jClient.get_instance()`.
- Docker Compose healthchecks are configured for all services; wait for them before running the seed.
