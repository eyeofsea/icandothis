# SCM Risk Hedging & TCO Comparison Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the SCM Risk Intelligence Platform to provide actionable hedging alternatives (routes & suppliers) with side-by-side TCO comparison reports, backed by dedicated PostgreSQL schemas per module and external data APIs, culminating in a Google Cloud production deployment.

**Architecture:** Four-phase approach: (1) PostgreSQL schema per module + migration framework, (2) Hedging engine with TCO comparison report API, (3) External data feed integrations for real-time pricing/risk data, (4) Google Cloud MCP deployment. Each phase produces working, testable software independently.

**Tech Stack:** FastAPI, PostgreSQL 16 (Alembic migrations), Neo4j 5.17, Next.js 14, Recharts, Google Cloud Run/Cloud SQL/Memorystore, Ollama (local LLM for cost estimation)

---

## Phase 1: PostgreSQL Module Schemas + Migration Framework

### Scope
Currently PostgreSQL exists in docker-compose but has no tables. We'll create dedicated schemas for each domain module with Alembic migrations.

---

### Task 1.1: Alembic Migration Setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/.gitkeep`
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add alembic dependency**

In `backend/requirements.txt`, add after the `asyncpg` line:

```
alembic==1.13.1
sqlalchemy[asyncio]==2.0.25
```

- [ ] **Step 2: Add SQLAlchemy database URL to config**

In `backend/app/config.py`, add these fields to the `Settings` class after the existing `POSTGRES_*` fields:

```python
    SQLALCHEMY_DATABASE_URL: str = "postgresql+asyncpg://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"
    SQLALCHEMY_SYNC_URL: str = "postgresql://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"
```

- [ ] **Step 3: Create alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://scmrisk:scmrisk2024@localhost:5432/scm_risk_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 4: Create alembic/env.py**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.database.models_pg import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=config.get_main_option("sqlalchemy.url").replace(
            "postgresql://", "postgresql+asyncpg://"
        ),
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Install dependencies and verify**

Run:
```bash
cd backend && pip install alembic==1.13.1 "sqlalchemy[asyncio]==2.0.25"
```

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic/ backend/requirements.txt backend/app/config.py
git commit -m "feat: add Alembic migration framework with async PostgreSQL support"
```

---

### Task 1.2: PostgreSQL Domain Models (SQLAlchemy)

**Files:**
- Create: `backend/app/database/models_pg.py`
- Create: `backend/app/database/session.py`

- [ ] **Step 1: Create SQLAlchemy session factory**

Create `backend/app/database/session.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: Create all domain models**

Create `backend/app/database/models_pg.py` with 6 schemas:

```python
"""
PostgreSQL domain models — one schema per module.

Schemas:
  - suppliers: supplier profiles, performance history, certifications
  - routes: shipping routes, transit records, cost history
  - equipment: equipment registry, delivery tracking
  - disruptions: disruption events, impact snapshots
  - tco: TCO calculations, scenario comparisons, hedging reports
  - audit: change log, decision records
"""
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, JSON, Enum, UniqueConstraint, Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── suppliers schema ──────────────────────────────────────────────

class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"
    __table_args__ = {"schema": "suppliers"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)  # SUP-NNN
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100))
    category = Column(String(50))  # OEM, Fabricator, etc.
    financial_rating = Column(Float)
    capacity_utilization = Column(Float)
    is_sanctioned = Column(Boolean, default=False)
    risk_flags = Column(ARRAY(String), default=[])
    certifications = Column(ARRAY(String), default=[])
    capabilities = Column(ARRAY(String), default=[])
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    performance_records = relationship("SupplierPerformance", back_populates="supplier")


class SupplierPerformance(Base):
    __tablename__ = "supplier_performance"
    __table_args__ = (
        Index("ix_supplier_perf_period", "supplier_id", "period_start"),
        {"schema": "suppliers"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.supplier_profiles.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    on_time_delivery_rate = Column(Float)
    quality_reject_rate = Column(Float)
    average_lead_time_days = Column(Integer)
    orders_completed = Column(Integer, default=0)
    total_value_delivered = Column(Numeric(15, 2), default=0)

    supplier = relationship("SupplierProfile", back_populates="performance_records")


# ── routes schema ─────────────────────────────────────────────────

class RouteRecord(Base):
    __tablename__ = "route_records"
    __table_args__ = {"schema": "routes"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)  # RT-NNN
    name = Column(String(200), nullable=False)
    origin_port = Column(String(100))
    destination_port = Column(String(100))
    distance_nm = Column(Float)
    base_transit_days = Column(Integer)
    base_shipping_cost = Column(Numeric(12, 2))
    base_insurance_cost = Column(Numeric(12, 2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    cost_history = relationship("RouteCostHistory", back_populates="route")


class RouteCostHistory(Base):
    __tablename__ = "route_cost_history"
    __table_args__ = (
        Index("ix_route_cost_date", "route_id", "recorded_date"),
        {"schema": "routes"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.route_records.id"), nullable=False)
    recorded_date = Column(Date, nullable=False)
    shipping_cost = Column(Numeric(12, 2))
    insurance_cost = Column(Numeric(12, 2))
    fuel_surcharge = Column(Numeric(12, 2))
    congestion_surcharge = Column(Numeric(12, 2))
    transit_days_actual = Column(Integer)
    source = Column(String(50))  # api_freightos, api_xeneta, manual

    route = relationship("RouteRecord", back_populates="cost_history")


# ── equipment schema ──────────────────────────────────────────────

class EquipmentRegistry(Base):
    __tablename__ = "equipment_registry"
    __table_args__ = {"schema": "equipment"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)  # EQ-NNNN
    name = Column(String(200), nullable=False)
    category = Column(String(50))
    criticality = Column(String(20))
    weight_kg = Column(Float)
    hs_code = Column(String(20))
    project_neo4j_id = Column(String(20), index=True)
    supplier_neo4j_id = Column(String(20), index=True)
    route_neo4j_id = Column(String(20), index=True)
    required_on_site_date = Column(Date)
    value_usd = Column(Numeric(15, 2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    delivery_events = relationship("DeliveryEvent", back_populates="equipment")


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"
    __table_args__ = (
        Index("ix_delivery_equip_date", "equipment_id", "event_date"),
        {"schema": "equipment"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.equipment_registry.id"), nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String(50))  # status_change, delay, inspection, customs_hold
    old_status = Column(String(50))
    new_status = Column(String(50))
    delay_days = Column(Integer, default=0)
    notes = Column(Text)

    equipment = relationship("EquipmentRegistry", back_populates="delivery_events")


# ── disruptions schema ────────────────────────────────────────────

class DisruptionRecord(Base):
    __tablename__ = "disruption_records"
    __table_args__ = {"schema": "disruptions"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)  # EVT-NNN
    name = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    affected_zone_ids = Column(ARRAY(String), default=[])
    source = Column(String(100))  # manual, api_gdelt, api_reliefweb
    raw_data = Column(JSONB)  # original API response
    created_at = Column(DateTime, server_default=func.now())

    impact_snapshots = relationship("ImpactSnapshot", back_populates="disruption")


class ImpactSnapshot(Base):
    __tablename__ = "impact_snapshots"
    __table_args__ = (
        Index("ix_impact_disruption_ts", "disruption_id", "snapshot_at"),
        {"schema": "disruptions"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disruption_id = Column(UUID(as_uuid=True), ForeignKey("disruptions.disruption_records.id"), nullable=False)
    snapshot_at = Column(DateTime, server_default=func.now())
    affected_equipment_count = Column(Integer, default=0)
    affected_project_count = Column(Integer, default=0)
    affected_route_count = Column(Integer, default=0)
    total_cost_impact = Column(Numeric(15, 2))
    estimated_delay_days = Column(Integer)
    impact_score = Column(Float)  # 0-10
    details = Column(JSONB)  # full impact analysis payload

    disruption = relationship("DisruptionRecord", back_populates="impact_snapshots")


# ── tco schema ────────────────────────────────────────────────────

class TCOReport(Base):
    __tablename__ = "tco_reports"
    __table_args__ = {"schema": "tco"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disruption_id = Column(UUID(as_uuid=True), ForeignKey("disruptions.disruption_records.id"), nullable=True)
    title = Column(String(300), nullable=False)
    created_by = Column(String(100), default="system")
    status = Column(String(20), default="draft")  # draft, published, archived
    baseline_tco = Column(JSONB, nullable=False)  # current TCO breakdown
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    scenarios = relationship("TCOScenario", back_populates="report")


class TCOScenario(Base):
    __tablename__ = "tco_scenarios"
    __table_args__ = {"schema": "tco"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("tco.tco_reports.id"), nullable=False)
    scenario_type = Column(String(50), nullable=False)  # reroute, supplier_switch, air_freight, hybrid, accept_delay
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Alternative details
    alternative_route_id = Column(String(20))  # RT-NNN if reroute
    alternative_supplier_id = Column(String(20))  # SUP-NNN if supplier switch
    affected_equipment_ids = Column(ARRAY(String), default=[])

    # Cost breakdown
    implementation_cost = Column(Numeric(15, 2), default=0)
    shipping_cost_delta = Column(Numeric(15, 2), default=0)
    insurance_cost_delta = Column(Numeric(15, 2), default=0)
    lead_time_delta_days = Column(Integer, default=0)
    delay_penalty_savings = Column(Numeric(15, 2), default=0)
    total_tco = Column(JSONB, nullable=False)  # full TCO breakdown

    # Comparison metrics
    tco_delta_vs_baseline = Column(Numeric(15, 2))  # positive = more expensive
    risk_reduction_pct = Column(Float, default=0)
    net_savings = Column(Numeric(15, 2))
    benefit_cost_ratio = Column(Float)
    recommendation_rank = Column(Integer)  # 1 = best

    created_at = Column(DateTime, server_default=func.now())

    report = relationship("TCOReport", back_populates="scenarios")


# ── audit schema ──────────────────────────────────────────────────

class DecisionLog(Base):
    __tablename__ = "decision_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tco_report_id = Column(UUID(as_uuid=True), ForeignKey("tco.tco_reports.id"), nullable=True)
    decision_type = Column(String(50))  # approve_reroute, approve_supplier_switch, reject, defer
    decided_by = Column(String(100))
    scenario_id = Column(UUID(as_uuid=True), nullable=True)
    rationale = Column(Text)
    decided_at = Column(DateTime, server_default=func.now())


class ChangeLog(Base):
    __tablename__ = "change_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # supplier, route, equipment, disruption
    entity_id = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String(100), default="system")
    changed_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/database/models_pg.py backend/app/database/session.py
git commit -m "feat: add SQLAlchemy domain models for 6 PostgreSQL schemas"
```

---

### Task 1.3: Initial Migration — Create All Schemas and Tables

**Files:**
- Create: `backend/alembic/versions/001_initial_schemas.py` (auto-generated)

- [ ] **Step 1: Create schemas in PostgreSQL**

```bash
cd backend
PGPASSWORD=scmrisk2024 psql -h localhost -U scmrisk -d scm_risk_db -c "
CREATE SCHEMA IF NOT EXISTS suppliers;
CREATE SCHEMA IF NOT EXISTS routes;
CREATE SCHEMA IF NOT EXISTS equipment;
CREATE SCHEMA IF NOT EXISTS disruptions;
CREATE SCHEMA IF NOT EXISTS tco;
CREATE SCHEMA IF NOT EXISTS audit;
"
```

- [ ] **Step 2: Generate initial migration**

```bash
cd backend && alembic revision --autogenerate -m "initial schemas and tables"
```

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: Verify tables exist**

```bash
PGPASSWORD=scmrisk2024 psql -h localhost -U scmrisk -d scm_risk_db -c "
SELECT schemaname, tablename FROM pg_tables
WHERE schemaname IN ('suppliers','routes','equipment','disruptions','tco','audit')
ORDER BY schemaname, tablename;
"
```

Expected: 12 tables across 6 schemas.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/
git commit -m "feat: initial migration — 6 schemas, 12 tables"
```

---

### Task 1.4: PostgreSQL Sync Script (Neo4j -> PostgreSQL)

**Files:**
- Create: `backend/app/database/sync_pg.py`

- [ ] **Step 1: Create sync script**

```python
"""
One-way sync: Neo4j (source of truth) -> PostgreSQL (analytics/reporting).
Runs at startup and can be triggered via API.
"""
from datetime import date

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.neo4j_client import neo4j_client
from app.database.session import async_session
from app.database.models_pg import (
    SupplierProfile, RouteRecord, EquipmentRegistry,
)


async def sync_suppliers() -> int:
    query = """
    MATCH (s:Supplier)
    OPTIONAL MATCH (s)-[:LOCATED_NEAR]->(p:Port)
    RETURN s.supplierId AS neo4j_id,
           s.name AS name,
           s.country AS country,
           s.city AS city,
           s.category AS category,
           s.financialRating AS financial_rating,
           s.capacityUtilization AS capacity_utilization,
           coalesce(s.riskFlags, []) AS risk_flags,
           coalesce(s.certifications, []) AS certifications,
           coalesce(s.capabilities, []) AS capabilities
    """
    records = await neo4j_client.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            stmt = pg_insert(SupplierProfile).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                country=r["country"] or "",
                city=r["city"],
                category=r["category"],
                financial_rating=r["financial_rating"],
                capacity_utilization=r["capacity_utilization"],
                is_sanctioned="sanctioned" in (r["risk_flags"] or []),
                risk_flags=r["risk_flags"] or [],
                certifications=r["certifications"] or [],
                capabilities=r["capabilities"] or [],
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "financial_rating": r["financial_rating"],
                    "capacity_utilization": r["capacity_utilization"],
                    "is_sanctioned": "sanctioned" in (r["risk_flags"] or []),
                    "risk_flags": r["risk_flags"] or [],
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_routes() -> int:
    query = """
    MATCH (r:ShippingRoute)
    OPTIONAL MATCH (r)-[:DEPARTS_FROM]->(op:Port)
    OPTIONAL MATCH (r)-[:ARRIVES_AT]->(dp:Port)
    RETURN r.routeId AS neo4j_id,
           r.name AS name,
           op.name AS origin_port,
           dp.name AS destination_port,
           r.totalDistanceNm AS distance_nm,
           r.estimatedTransitDays AS base_transit_days,
           r.shippingCost AS base_shipping_cost,
           r.insuranceCost AS base_insurance_cost
    """
    records = await neo4j_client.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            stmt = pg_insert(RouteRecord).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                origin_port=r["origin_port"],
                destination_port=r["destination_port"],
                distance_nm=r["distance_nm"],
                base_transit_days=r["base_transit_days"],
                base_shipping_cost=r["base_shipping_cost"],
                base_insurance_cost=r["base_insurance_cost"],
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "base_transit_days": r["base_transit_days"],
                    "base_shipping_cost": r["base_shipping_cost"],
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_equipment() -> int:
    query = """
    MATCH (e:Equipment)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    RETURN e.equipmentId AS neo4j_id,
           e.name AS name,
           e.category AS category,
           e.criticality AS criticality,
           e.weight AS weight_kg,
           e.hsCode AS hs_code,
           p.projectId AS project_neo4j_id,
           s.supplierId AS supplier_neo4j_id,
           r.routeId AS route_neo4j_id,
           e.requiredOnSiteDate AS required_on_site_date
    """
    records = await neo4j_client.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            stmt = pg_insert(EquipmentRegistry).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                category=r["category"],
                criticality=r["criticality"],
                weight_kg=r["weight_kg"],
                hs_code=r["hs_code"],
                project_neo4j_id=r["project_neo4j_id"],
                supplier_neo4j_id=r["supplier_neo4j_id"],
                route_neo4j_id=r["route_neo4j_id"],
                required_on_site_date=r["required_on_site_date"],
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "criticality": r["criticality"],
                    "supplier_neo4j_id": r["supplier_neo4j_id"],
                    "route_neo4j_id": r["route_neo4j_id"],
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_all() -> dict:
    suppliers = await sync_suppliers()
    routes = await sync_routes()
    equipment = await sync_equipment()
    return {"suppliers": suppliers, "routes": routes, "equipment": equipment}
```

- [ ] **Step 2: Wire sync into app startup**

In `backend/app/main.py`, add to the lifespan handler after Neo4j seed, before yield:

```python
    from app.database.sync_pg import sync_all
    sync_result = await sync_all()
    logger.info(f"PostgreSQL sync complete: {sync_result}")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/database/sync_pg.py backend/app/main.py
git commit -m "feat: add Neo4j -> PostgreSQL sync for suppliers, routes, equipment"
```

---

## Phase 2: Hedging Engine & TCO Comparison Report

### Scope
Build the core hedging recommendation engine and TCO comparison report API. When a disruption occurs, the system generates alternative routes and suppliers, calculates full TCO for each option, and produces a decision-ready report.

---

### Task 2.1: TCO Calculation Engine

**Files:**
- Create: `backend/app/services/tco_engine.py`
- Test: `backend/tests/test_tco_engine.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_tco_engine.py`:

```python
import pytest
from decimal import Decimal
from app.services.tco_engine import calculate_baseline_tco, calculate_scenario_tco, compare_tco


def make_equipment(criticality="Critical", weight_kg=50000, value_usd=2000000, delay_days=30):
    return {
        "equipmentId": "EQ-0001",
        "name": "Test Turbine",
        "criticality": criticality,
        "weight": weight_kg,
        "value": value_usd,
        "requiredOnSiteDate": "2026-06-01",
    }


def make_route(shipping_cost=285000, insurance_cost=42000, transit_days=32):
    return {
        "routeId": "RT-001",
        "name": "Houston to Jebel Ali",
        "shippingCost": shipping_cost,
        "insuranceCost": insurance_cost,
        "estimatedTransitDays": transit_days,
    }


def make_project(total_value=500000000):
    return {
        "projectId": "PRJ-001",
        "name": "Jafurah Gas",
        "totalValue": total_value,
    }


class TestBaselineTCO:
    def test_includes_all_cost_components(self):
        result = calculate_baseline_tco(
            equipment=[make_equipment()],
            route=make_route(),
            project=make_project(),
            delay_days=30,
        )
        assert "shipping_cost" in result
        assert "insurance_cost" in result
        assert "delay_penalties" in result
        assert "site_overhead" in result
        assert "storage_cost" in result
        assert "total" in result
        assert result["total"] > 0

    def test_zero_delay_no_penalties(self):
        result = calculate_baseline_tco(
            equipment=[make_equipment()],
            route=make_route(),
            project=make_project(),
            delay_days=0,
        )
        assert result["delay_penalties"] == 0
        assert result["site_overhead"] == 0

    def test_critical_equipment_higher_storage(self):
        critical = calculate_baseline_tco(
            equipment=[make_equipment(criticality="Critical", weight_kg=60000)],
            route=make_route(),
            project=make_project(),
            delay_days=30,
        )
        low = calculate_baseline_tco(
            equipment=[make_equipment(criticality="Low", weight_kg=60000)],
            route=make_route(),
            project=make_project(),
            delay_days=30,
        )
        assert critical["storage_cost"] > low["storage_cost"]


class TestScenarioTCO:
    def test_reroute_scenario(self):
        baseline = calculate_baseline_tco(
            equipment=[make_equipment()],
            route=make_route(),
            project=make_project(),
            delay_days=30,
        )
        alt_route = make_route(shipping_cost=450000, insurance_cost=60000, transit_days=45)
        result = calculate_scenario_tco(
            baseline=baseline,
            equipment=[make_equipment()],
            project=make_project(),
            scenario_type="reroute",
            alternative_route=alt_route,
            original_delay_days=30,
            residual_delay_days=5,
        )
        assert result["shipping_cost"] == 450000
        assert result["insurance_cost"] == 60000
        assert result["residual_delay_days"] == 5
        assert "total" in result

    def test_supplier_switch_scenario(self):
        baseline = calculate_baseline_tco(
            equipment=[make_equipment()],
            route=make_route(),
            project=make_project(),
            delay_days=30,
        )
        alt_supplier = {
            "supplierId": "SUP-050",
            "averageLeadTime": 45,
            "qualificationDays": 14,
            "costPremiumPct": 0.10,
        }
        result = calculate_scenario_tco(
            baseline=baseline,
            equipment=[make_equipment()],
            project=make_project(),
            scenario_type="supplier_switch",
            alternative_supplier=alt_supplier,
            original_delay_days=30,
            residual_delay_days=10,
        )
        assert result["qualification_cost"] > 0
        assert "total" in result


class TestCompareTCO:
    def test_ranks_by_net_savings(self):
        baseline = {"total": 5000000, "delay_penalties": 2000000}
        scenarios = [
            {"name": "Reroute", "total": 3500000, "implementation_cost": 200000},
            {"name": "Air Freight", "total": 4200000, "implementation_cost": 800000},
            {"name": "Supplier Switch", "total": 3000000, "implementation_cost": 500000},
        ]
        result = compare_tco(baseline, scenarios)
        assert result[0]["name"] == "Supplier Switch"  # best net savings
        assert result[0]["rank"] == 1
        assert all("net_savings" in s for s in result)
        assert all("benefit_cost_ratio" in s for s in result)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_tco_engine.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Implement TCO engine**

Create `backend/app/services/tco_engine.py`:

```python
"""
Pure-function TCO calculation engine.
No database access — takes data in, returns numbers out.
"""
from typing import Any

# Cost constants
SITE_OVERHEAD_PER_DAY = 50_000
IDLE_WORKFORCE_PER_DAY = 25_000
LD_RATE_PCT_PER_WEEK = 0.5  # % of project value
LD_CAP_PCT = 10.0
STORAGE_RATES = {  # USD/day by weight tier
    100_000: 2_000,  # >100t
    50_000: 1_000,   # >50t
    0: 500,          # base
}
CRITICAL_STORAGE_MULTIPLIER = 1.5
QUALIFICATION_COST_PER_DAY = 5_000


def _storage_rate(weight_kg: float, criticality: str) -> float:
    base = 500
    for threshold, rate in sorted(STORAGE_RATES.items(), reverse=True):
        if weight_kg >= threshold:
            base = rate
            break
    if criticality in ("Critical", "critical"):
        base *= CRITICAL_STORAGE_MULTIPLIER
    return base


def calculate_baseline_tco(
    equipment: list[dict[str, Any]],
    route: dict[str, Any],
    project: dict[str, Any],
    delay_days: int,
) -> dict[str, Any]:
    shipping_cost = route.get("shippingCost", 0)
    insurance_cost = route.get("insuranceCost", 0)

    # Delay penalties (LD)
    project_value = project.get("totalValue", 0)
    if delay_days > 0 and project_value > 0:
        weekly_penalty = project_value * (LD_RATE_PCT_PER_WEEK / 100)
        raw_penalty = weekly_penalty * (delay_days / 7)
        delay_penalties = min(raw_penalty, project_value * (LD_CAP_PCT / 100))
    else:
        delay_penalties = 0

    site_overhead = SITE_OVERHEAD_PER_DAY * delay_days
    idle_workforce = IDLE_WORKFORCE_PER_DAY * delay_days

    storage_cost = 0
    for eq in equipment:
        weight = eq.get("weight", 0)
        crit = eq.get("criticality", "Medium")
        storage_cost += _storage_rate(weight, crit) * delay_days

    total = shipping_cost + insurance_cost + delay_penalties + site_overhead + idle_workforce + storage_cost

    return {
        "shipping_cost": shipping_cost,
        "insurance_cost": insurance_cost,
        "delay_penalties": delay_penalties,
        "site_overhead": site_overhead,
        "idle_workforce": idle_workforce,
        "storage_cost": storage_cost,
        "delay_days": delay_days,
        "total": total,
    }


def calculate_scenario_tco(
    baseline: dict[str, Any],
    equipment: list[dict[str, Any]],
    project: dict[str, Any],
    scenario_type: str,
    original_delay_days: int,
    residual_delay_days: int,
    alternative_route: dict[str, Any] | None = None,
    alternative_supplier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "scenario_type": scenario_type,
        "original_delay_days": original_delay_days,
        "residual_delay_days": residual_delay_days,
    }

    if scenario_type == "reroute" and alternative_route:
        result["shipping_cost"] = alternative_route.get("shippingCost", 0)
        result["insurance_cost"] = alternative_route.get("insuranceCost", 0)
        result["transit_days_delta"] = (
            alternative_route.get("estimatedTransitDays", 0)
            - baseline.get("delay_days", 0)
        )
        result["implementation_cost"] = abs(
            result["shipping_cost"] - baseline["shipping_cost"]
        ) + abs(result["insurance_cost"] - baseline["insurance_cost"])
        result["qualification_cost"] = 0

    elif scenario_type == "supplier_switch" and alternative_supplier:
        cost_premium = alternative_supplier.get("costPremiumPct", 0)
        eq_total_value = sum(eq.get("value", 0) for eq in equipment)
        result["shipping_cost"] = baseline["shipping_cost"]
        result["insurance_cost"] = baseline["insurance_cost"]
        result["supplier_premium"] = eq_total_value * cost_premium
        qual_days = alternative_supplier.get("qualificationDays", 14)
        result["qualification_cost"] = qual_days * QUALIFICATION_COST_PER_DAY
        result["implementation_cost"] = result["supplier_premium"] + result["qualification_cost"]

    elif scenario_type == "air_freight":
        total_weight_kg = sum(eq.get("weight", 0) for eq in equipment)
        result["shipping_cost"] = total_weight_kg * 8  # $8/kg
        result["insurance_cost"] = baseline["insurance_cost"] * 1.5
        result["implementation_cost"] = result["shipping_cost"]
        result["qualification_cost"] = 0

    else:
        result["shipping_cost"] = baseline.get("shipping_cost", 0)
        result["insurance_cost"] = baseline.get("insurance_cost", 0)
        result["implementation_cost"] = 0
        result["qualification_cost"] = 0

    # Recalculate delay-dependent costs with residual delay
    project_value = project.get("totalValue", 0)
    if residual_delay_days > 0 and project_value > 0:
        weekly_penalty = project_value * (LD_RATE_PCT_PER_WEEK / 100)
        raw_penalty = weekly_penalty * (residual_delay_days / 7)
        result["delay_penalties"] = min(raw_penalty, project_value * (LD_CAP_PCT / 100))
    else:
        result["delay_penalties"] = 0

    result["site_overhead"] = SITE_OVERHEAD_PER_DAY * residual_delay_days
    result["idle_workforce"] = IDLE_WORKFORCE_PER_DAY * residual_delay_days

    storage_cost = 0
    for eq in equipment:
        storage_cost += _storage_rate(eq.get("weight", 0), eq.get("criticality", "Medium")) * residual_delay_days
    result["storage_cost"] = storage_cost

    result["total"] = (
        result.get("shipping_cost", 0)
        + result.get("insurance_cost", 0)
        + result.get("implementation_cost", 0)
        + result["delay_penalties"]
        + result["site_overhead"]
        + result["idle_workforce"]
        + result["storage_cost"]
    )

    return result


def compare_tco(
    baseline: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_total = baseline["total"]
    ranked = []
    for s in scenarios:
        scenario_total = s["total"]
        impl_cost = s.get("implementation_cost", 0)
        net_savings = baseline_total - scenario_total
        bcr = (net_savings / impl_cost) if impl_cost > 0 else float("inf")
        ranked.append({
            **s,
            "baseline_total": baseline_total,
            "net_savings": net_savings,
            "savings_pct": (net_savings / baseline_total * 100) if baseline_total > 0 else 0,
            "benefit_cost_ratio": round(bcr, 2),
        })

    ranked.sort(key=lambda x: x["net_savings"], reverse=True)
    for i, s in enumerate(ranked):
        s["rank"] = i + 1

    return ranked
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_tco_engine.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tco_engine.py backend/tests/test_tco_engine.py
git commit -m "feat: pure-function TCO calculation engine with baseline/scenario/comparison"
```

---

### Task 2.2: Hedging Report Service

**Files:**
- Create: `backend/app/services/hedging_service.py`
- Test: `backend/tests/test_hedging_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_hedging_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.hedging_service import HedgingService


@pytest.fixture
def hedging_service():
    return HedgingService()


class TestGenerateHedgingReport:
    @pytest.mark.asyncio
    async def test_returns_report_structure(self, hedging_service):
        with patch.object(hedging_service, "_fetch_disruption_context") as mock_ctx:
            mock_ctx.return_value = {
                "event": {"eventId": "EVT-001", "severity": 5, "type": "geopolitical"},
                "affected_equipment": [
                    {"equipmentId": "EQ-0001", "name": "Turbine", "criticality": "Critical",
                     "weight": 80000, "value": 2000000, "supplierId": "SUP-001", "routeId": "RT-001"},
                ],
                "affected_routes": [
                    {"routeId": "RT-001", "name": "Houston-Gulf", "shippingCost": 285000,
                     "insuranceCost": 42000, "estimatedTransitDays": 32, "currentStatus": "blocked"},
                ],
                "affected_projects": [
                    {"projectId": "PRJ-001", "name": "Jafurah", "totalValue": 500000000},
                ],
                "alternative_routes": [
                    {"routeId": "RT-ALT1", "name": "Cape Route", "shippingCost": 450000,
                     "insuranceCost": 60000, "estimatedTransitDays": 55, "additionalDays": 23},
                ],
                "alternative_suppliers": [
                    {"supplierId": "SUP-050", "name": "Doosan", "averageLeadTime": 45,
                     "costPremiumPct": 0.08, "qualificationDays": 14},
                ],
            }
            report = await hedging_service.generate_report("EVT-001", delay_days=30)

            assert report["disruption_id"] == "EVT-001"
            assert "baseline_tco" in report
            assert "scenarios" in report
            assert len(report["scenarios"]) >= 2  # at least reroute + supplier_switch
            assert report["scenarios"][0]["rank"] == 1  # ranked
            assert "executive_summary" in report
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_hedging_service.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement hedging service**

Create `backend/app/services/hedging_service.py`:

```python
"""
Orchestrates hedging alternatives and TCO comparison reports.
Pulls data from Neo4j agents, calculates TCO via tco_engine, persists to PostgreSQL.
"""
from typing import Any, Optional

from app.database.neo4j_client import neo4j_client
from app.services.tco_engine import calculate_baseline_tco, calculate_scenario_tco, compare_tco


class HedgingService:
    async def generate_report(
        self,
        disruption_id: str,
        delay_days: int = 30,
        include_air_freight: bool = True,
    ) -> dict[str, Any]:
        ctx = await self._fetch_disruption_context(disruption_id)
        event = ctx["event"]
        equipment = ctx["affected_equipment"]
        projects = ctx["affected_projects"]
        alt_routes = ctx["alternative_routes"]
        alt_suppliers = ctx["alternative_suppliers"]

        # Use first affected project for LD calculations (largest impact)
        primary_project = max(projects, key=lambda p: p.get("totalValue", 0)) if projects else {}
        primary_route = ctx["affected_routes"][0] if ctx["affected_routes"] else {}

        # 1. Baseline TCO (no action)
        baseline = calculate_baseline_tco(
            equipment=equipment,
            route=primary_route,
            project=primary_project,
            delay_days=delay_days,
        )

        # 2. Build scenarios
        scenarios = []

        # Reroute scenarios
        for alt in alt_routes[:3]:  # top 3
            additional_days = alt.get("additionalDays", 0)
            residual = max(0, delay_days - (delay_days - additional_days))
            scenario = calculate_scenario_tco(
                baseline=baseline,
                equipment=equipment,
                project=primary_project,
                scenario_type="reroute",
                alternative_route=alt,
                original_delay_days=delay_days,
                residual_delay_days=min(additional_days, delay_days),
            )
            scenario["name"] = f"Reroute: {alt.get('name', alt.get('routeId', ''))}"
            scenario["alternative_id"] = alt.get("routeId")
            scenario["alternative_details"] = alt
            scenarios.append(scenario)

        # Supplier switch scenarios
        for alt in alt_suppliers[:3]:  # top 3
            qual_days = alt.get("qualificationDays", 14)
            lt_delta = max(0, alt.get("averageLeadTime", 30) - 30)
            residual = min(delay_days, qual_days + lt_delta)
            scenario = calculate_scenario_tco(
                baseline=baseline,
                equipment=equipment,
                project=primary_project,
                scenario_type="supplier_switch",
                alternative_supplier=alt,
                original_delay_days=delay_days,
                residual_delay_days=residual,
            )
            scenario["name"] = f"Supplier: {alt.get('name', alt.get('supplierId', ''))}"
            scenario["alternative_id"] = alt.get("supplierId")
            scenario["alternative_details"] = alt
            scenarios.append(scenario)

        # Air freight (for items <5 tons)
        if include_air_freight:
            light_equipment = [eq for eq in equipment if eq.get("weight", 0) < 5000]
            if light_equipment:
                scenario = calculate_scenario_tco(
                    baseline=baseline,
                    equipment=light_equipment,
                    project=primary_project,
                    scenario_type="air_freight",
                    original_delay_days=delay_days,
                    residual_delay_days=3,
                )
                scenario["name"] = f"Air Freight ({len(light_equipment)} items)"
                scenarios.append(scenario)

        # Accept delay (baseline)
        accept = calculate_scenario_tco(
            baseline=baseline,
            equipment=equipment,
            project=primary_project,
            scenario_type="accept_delay",
            original_delay_days=delay_days,
            residual_delay_days=delay_days,
        )
        accept["name"] = "Accept Delay (No Action)"
        scenarios.append(accept)

        # 3. Rank scenarios
        ranked = compare_tco(baseline, scenarios)

        # 4. Executive summary
        best = ranked[0] if ranked else None
        summary = self._build_summary(event, baseline, best, len(equipment), len(projects))

        return {
            "disruption_id": disruption_id,
            "disruption_name": event.get("name", ""),
            "severity": event.get("severity", 0),
            "delay_days": delay_days,
            "affected_equipment_count": len(equipment),
            "affected_project_count": len(projects),
            "baseline_tco": baseline,
            "scenarios": ranked,
            "executive_summary": summary,
        }

    async def _fetch_disruption_context(self, disruption_id: str) -> dict[str, Any]:
        # Fetch event
        event_q = """
        MATCH (d:DisruptionEvent {eventId: $eventId})
        OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
        RETURN d {.*} AS event, collect(z.zoneId) AS zoneIds
        """
        event_records = await neo4j_client.execute_read(event_q, {"eventId": disruption_id})
        event = event_records[0]["event"] if event_records else {}
        zone_ids = event_records[0]["zoneIds"] if event_records else []

        # Fetch affected equipment via zones -> routes -> equipment
        equip_q = """
        MATCH (z:GeopoliticalZone)<-[:PASSES_THROUGH]-(r:ShippingRoute)<-[:SHIPPED_VIA]-(e:Equipment)
        WHERE z.zoneId IN $zoneIds
        OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
        OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
        RETURN DISTINCT e {.*, projectId: p.projectId, supplierId: s.supplierId, routeId: r.routeId} AS equipment
        """
        equip_records = await neo4j_client.execute_read(equip_q, {"zoneIds": zone_ids})
        equipment = [r["equipment"] for r in equip_records]

        # Fetch affected routes
        route_q = """
        MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
        WHERE z.zoneId IN $zoneIds
        RETURN DISTINCT r {.*} AS route
        """
        route_records = await neo4j_client.execute_read(route_q, {"zoneIds": zone_ids})
        affected_routes = [r["route"] for r in route_records]

        # Fetch affected projects
        project_q = """
        MATCH (p:Project)-[:HAS_EQUIPMENT]->(e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
        WHERE z.zoneId IN $zoneIds
        RETURN DISTINCT p {.*} AS project
        """
        proj_records = await neo4j_client.execute_read(project_q, {"zoneIds": zone_ids})
        projects = [r["project"] for r in proj_records]

        # Find alternative routes (avoiding disrupted zones)
        alt_route_q = """
        MATCH (alt:ShippingRoute)
        WHERE alt.currentStatus IN ['active', 'planned']
          AND NOT EXISTS {
            MATCH (alt)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
            WHERE z.zoneId IN $zoneIds
          }
        RETURN alt {.*} AS route
        ORDER BY alt.estimatedTransitDays ASC
        LIMIT 5
        """
        alt_route_records = await neo4j_client.execute_read(alt_route_q, {"zoneIds": zone_ids})
        alt_routes = [r["route"] for r in alt_route_records]

        # Find alternative suppliers (outside disrupted zones)
        categories = list({eq.get("category") for eq in equipment if eq.get("category")})
        alt_suppliers = []
        for cat in categories[:3]:
            sup_q = """
            MATCH (s:Supplier)-[:SUPPLIES]->(e:Equipment)
            WHERE e.category = $category
              AND NOT EXISTS {
                MATCH (s)-[:LOCATED_IN]->(z:GeopoliticalZone)
                WHERE z.zoneId IN $zoneIds
              }
            RETURN DISTINCT s {.*} AS supplier
            ORDER BY s.onTimeDeliveryRate DESC
            LIMIT 3
            """
            sup_records = await neo4j_client.execute_read(sup_q, {"category": cat, "zoneIds": zone_ids})
            alt_suppliers.extend([r["supplier"] for r in sup_records])

        return {
            "event": event,
            "affected_equipment": equipment,
            "affected_routes": affected_routes,
            "affected_projects": projects,
            "alternative_routes": alt_routes,
            "alternative_suppliers": alt_suppliers,
        }

    def _build_summary(
        self,
        event: dict,
        baseline: dict,
        best_scenario: dict | None,
        equipment_count: int,
        project_count: int,
    ) -> str:
        lines = [
            f"Disruption: {event.get('name', 'Unknown')} (Severity {event.get('severity', '?')}/5)",
            f"Impact: {equipment_count} equipment items across {project_count} projects",
            f"No-Action Cost: ${baseline['total']:,.0f}",
        ]
        if best_scenario:
            lines.append(
                f"Recommended: {best_scenario['name']} "
                f"(saves ${best_scenario['net_savings']:,.0f}, "
                f"BCR {best_scenario['benefit_cost_ratio']:.1f}x)"
            )
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_hedging_service.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/hedging_service.py backend/tests/test_hedging_service.py
git commit -m "feat: hedging report service — orchestrates alternatives + TCO comparison"
```

---

### Task 2.3: Hedging Report API Endpoints

**Files:**
- Create: `backend/app/routers/hedging.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Create hedging router**

Create `backend/app/routers/hedging.py`:

```python
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.hedging_service import HedgingService

router = APIRouter(prefix="/api/hedging", tags=["hedging"])
hedging_service = HedgingService()


@router.get("/report/{disruption_id}")
async def get_hedging_report(
    disruption_id: str,
    delay_days: int = Query(default=30, ge=1, le=365),
    include_air_freight: bool = Query(default=True),
):
    """Generate a hedging report with alternative routes/suppliers and TCO comparison."""
    try:
        report = await hedging_service.generate_report(
            disruption_id=disruption_id,
            delay_days=delay_days,
            include_air_freight=include_air_freight,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{disruption_id}")
async def get_tco_comparison(
    disruption_id: str,
    delay_days: int = Query(default=30, ge=1, le=365),
):
    """Get only the TCO comparison table (lighter payload for decision dashboard)."""
    report = await hedging_service.generate_report(
        disruption_id=disruption_id,
        delay_days=delay_days,
    )
    return {
        "disruption_id": disruption_id,
        "baseline_total": report["baseline_tco"]["total"],
        "scenarios": [
            {
                "rank": s["rank"],
                "name": s["name"],
                "scenario_type": s["scenario_type"],
                "total_tco": s["total"],
                "net_savings": s["net_savings"],
                "savings_pct": s["savings_pct"],
                "benefit_cost_ratio": s["benefit_cost_ratio"],
                "residual_delay_days": s["residual_delay_days"],
            }
            for s in report["scenarios"]
        ],
        "executive_summary": report["executive_summary"],
    }
```

- [ ] **Step 2: Register router in main.py**

In `backend/app/main.py`, add with other router imports:

```python
from app.routers.hedging import router as hedging_router
```

And register it:

```python
app.include_router(hedging_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/hedging.py backend/app/main.py
git commit -m "feat: add /api/hedging/report and /api/hedging/compare endpoints"
```

---

### Task 2.4: Frontend — TCO Comparison Report View

**Files:**
- Create: `frontend/src/views/HedgingReportView.tsx`
- Modify: `frontend/src/lib/api.ts` (add hedging API calls)
- Modify: `frontend/src/lib/types.ts` (add HedgingReport type)
- Modify: `frontend/src/app/page.tsx` (add navigation entry)
- Modify: `frontend/src/components/layout/Sidebar.tsx` (add menu item)

- [ ] **Step 1: Add types**

In `frontend/src/lib/types.ts`, add at the end:

```typescript
// Hedging Report
export interface TCOBreakdown {
  shipping_cost: number;
  insurance_cost: number;
  delay_penalties: number;
  site_overhead: number;
  idle_workforce: number;
  storage_cost: number;
  total: number;
  delay_days: number;
}

export interface HedgingScenario {
  rank: number;
  name: string;
  scenario_type: string;
  total: number;
  net_savings: number;
  savings_pct: number;
  benefit_cost_ratio: number;
  implementation_cost: number;
  residual_delay_days: number;
  alternative_id?: string;
  alternative_details?: Record<string, unknown>;
}

export interface HedgingReport {
  disruption_id: string;
  disruption_name: string;
  severity: number;
  delay_days: number;
  affected_equipment_count: number;
  affected_project_count: number;
  baseline_tco: TCOBreakdown;
  scenarios: HedgingScenario[];
  executive_summary: string;
}
```

- [ ] **Step 2: Add API functions**

In `frontend/src/lib/api.ts`, add:

```typescript
export async function fetchHedgingReport(
  disruptionId: string,
  delayDays: number = 30,
): Promise<HedgingReport> {
  return apiFetch<HedgingReport>(
    `/api/hedging/report/${disruptionId}?delay_days=${delayDays}`
  );
}
```

- [ ] **Step 3: Create HedgingReportView**

Create `frontend/src/views/HedgingReportView.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import { useDisruptionStore } from "@/stores/disruptionStore";
import type { HedgingReport, HedgingScenario, TCOBreakdown } from "@/lib/types";
import { fetchHedgingReport } from "@/lib/api";

const COLORS = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function SeverityBadge({ severity }: { severity: number }) {
  const colors = ["", "bg-blue-500", "bg-yellow-500", "bg-orange-500", "bg-red-500", "bg-red-700"];
  return (
    <span className={`${colors[severity]} text-white text-xs px-2 py-0.5 rounded`}>
      Severity {severity}/5
    </span>
  );
}

function BaselineTCOCard({ tco }: { tco: TCOBreakdown }) {
  const pieData = [
    { name: "Shipping", value: tco.shipping_cost, fill: "#3b82f6" },
    { name: "Insurance", value: tco.insurance_cost, fill: "#06b6d4" },
    { name: "Delay Penalties", value: tco.delay_penalties, fill: "#ef4444" },
    { name: "Site Overhead", value: tco.site_overhead, fill: "#f59e0b" },
    { name: "Workforce", value: tco.idle_workforce, fill: "#8b5cf6" },
    { name: "Storage", value: tco.storage_cost, fill: "#64748b" },
  ].filter((d) => d.value > 0);

  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-1">Baseline TCO (No Action)</h3>
      <p className="text-3xl font-bold text-red-400 mb-4">{formatCurrency(tco.total)}</p>
      <p className="text-xs text-gray-500 mb-3">{tco.delay_days} days delay</p>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%"
            innerRadius={50} outerRadius={80} paddingAngle={2}>
            {pieData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => formatCurrency(v)} />
          <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScenarioComparisonChart({ scenarios, baselineTotal }: {
  scenarios: HedgingScenario[];
  baselineTotal: number;
}) {
  const data = scenarios.map((s) => ({
    name: s.name.length > 25 ? s.name.slice(0, 22) + "..." : s.name,
    "Total TCO": s.total,
    "Net Savings": Math.max(0, s.net_savings),
    rank: s.rank,
  }));

  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4">TCO Comparison by Scenario</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 120 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis type="number" tickFormatter={formatCurrency} stroke="#6b7280" />
          <YAxis type="category" dataKey="name" stroke="#6b7280" width={120} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v: number) => formatCurrency(v)} />
          <Legend />
          <Bar dataKey="Total TCO" fill="#ef4444" radius={[0, 4, 4, 0]} />
          <Bar dataKey="Net Savings" fill="#22c55e" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
        <span className="inline-block w-3 h-3 bg-red-400/30 border border-red-400 rounded" />
        <span>Baseline: {formatCurrency(baselineTotal)}</span>
      </div>
    </div>
  );
}

function ScenarioTable({ scenarios }: { scenarios: HedgingScenario[] }) {
  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5 overflow-x-auto">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Decision Matrix</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 border-b border-white/10">
            <th className="text-left py-2 px-2">#</th>
            <th className="text-left py-2 px-2">Scenario</th>
            <th className="text-right py-2 px-2">Total TCO</th>
            <th className="text-right py-2 px-2">Net Savings</th>
            <th className="text-right py-2 px-2">Savings %</th>
            <th className="text-right py-2 px-2">BCR</th>
            <th className="text-right py-2 px-2">Impl. Cost</th>
            <th className="text-right py-2 px-2">Residual Delay</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr key={s.rank} className={`border-b border-white/5 ${s.rank === 1 ? "bg-green-500/10" : ""}`}>
              <td className="py-2 px-2 text-gray-400">{s.rank}</td>
              <td className="py-2 px-2 text-white font-medium">
                {s.name}
                {s.rank === 1 && (
                  <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">
                    Recommended
                  </span>
                )}
              </td>
              <td className="py-2 px-2 text-right text-white">{formatCurrency(s.total)}</td>
              <td className={`py-2 px-2 text-right ${s.net_savings > 0 ? "text-green-400" : "text-red-400"}`}>
                {s.net_savings > 0 ? "+" : ""}{formatCurrency(s.net_savings)}
              </td>
              <td className="py-2 px-2 text-right text-gray-300">{s.savings_pct.toFixed(1)}%</td>
              <td className="py-2 px-2 text-right text-gray-300">{s.benefit_cost_ratio}x</td>
              <td className="py-2 px-2 text-right text-yellow-400">{formatCurrency(s.implementation_cost)}</td>
              <td className="py-2 px-2 text-right text-gray-300">{s.residual_delay_days}d</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HedgingReportView() {
  const { activeDisruptions } = useDisruptionStore();
  const [report, setReport] = useState<HedgingReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDisruption, setSelectedDisruption] = useState<string>("");
  const [delayDays, setDelayDays] = useState(30);

  useEffect(() => {
    if (activeDisruptions.length > 0 && !selectedDisruption) {
      setSelectedDisruption(activeDisruptions[0].id);
    }
  }, [activeDisruptions, selectedDisruption]);

  const handleGenerate = async () => {
    if (!selectedDisruption) return;
    setLoading(true);
    try {
      const data = await fetchHedgingReport(selectedDisruption, delayDays);
      setReport(data);
    } catch (err) {
      console.error("Failed to generate hedging report:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Hedging & TCO Report</h2>
          <p className="text-sm text-gray-400 mt-1">
            Compare alternative routes and suppliers with full TCO breakdown
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-end gap-4 bg-[#111827]/80 border border-white/10 rounded-xl p-4">
        <div className="flex-1">
          <label className="text-xs text-gray-400 block mb-1">Disruption Event</label>
          <select
            value={selectedDisruption}
            onChange={(e) => setSelectedDisruption(e.target.value)}
            className="w-full bg-[#0a0e1a] border border-white/20 rounded px-3 py-2 text-sm text-white"
          >
            <option value="">Select disruption...</option>
            {activeDisruptions.map((d) => (
              <option key={d.id} value={d.id}>{d.name} (Sev. {d.severity})</option>
            ))}
          </select>
        </div>
        <div className="w-32">
          <label className="text-xs text-gray-400 block mb-1">Delay (days)</label>
          <input
            type="number"
            value={delayDays}
            onChange={(e) => setDelayDays(parseInt(e.target.value) || 30)}
            min={1}
            max={365}
            className="w-full bg-[#0a0e1a] border border-white/20 rounded px-3 py-2 text-sm text-white"
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !selectedDisruption}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-6 py-2 rounded text-sm font-medium"
        >
          {loading ? "Generating..." : "Generate Report"}
        </button>
      </div>

      {/* Report Content */}
      {report && (
        <>
          {/* Executive Summary */}
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-sm font-medium text-white">Executive Summary</h3>
              <SeverityBadge severity={report.severity} />
            </div>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
              {report.executive_summary}
            </pre>
            <div className="flex gap-4 mt-3 text-xs text-gray-500">
              <span>{report.affected_equipment_count} equipment affected</span>
              <span>{report.affected_project_count} projects at risk</span>
            </div>
          </div>

          {/* TCO Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <BaselineTCOCard tco={report.baseline_tco} />
            <div className="lg:col-span-2">
              <ScenarioComparisonChart
                scenarios={report.scenarios}
                baselineTotal={report.baseline_tco.total}
              />
            </div>
          </div>

          {/* Decision Matrix */}
          <ScenarioTable scenarios={report.scenarios} />
        </>
      )}

      {/* Empty state */}
      {!report && !loading && (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">No report generated yet</p>
          <p className="text-sm">Select a disruption event and click Generate Report</p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Add Hedging view to navigation**

In `frontend/src/components/layout/Sidebar.tsx`, add a new navigation item after the existing Impact entry:

```typescript
{ id: "hedging", label: "Hedging Report", icon: "scale" }
```

In `frontend/src/app/page.tsx`, add the import and view mapping:

```typescript
import HedgingReportView from "@/views/HedgingReportView";
```

And in the view rendering logic:

```typescript
case "hedging":
  return <HedgingReportView />;
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/HedgingReportView.tsx frontend/src/lib/api.ts frontend/src/lib/types.ts frontend/src/app/page.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: hedging report view — TCO comparison dashboard with charts and decision matrix"
```

---

## Phase 3: External Data Feed APIs

### Scope
Integrate real external APIs for maritime freight rates, geopolitical risk, and supplier intelligence to replace hardcoded values with live data.

---

### Task 3.1: External Feed Service Framework

**Files:**
- Create: `backend/app/services/external_feeds/base.py`
- Create: `backend/app/services/external_feeds/freight_feed.py`
- Create: `backend/app/services/external_feeds/risk_feed.py`
- Create: `backend/app/services/external_feeds/sanctions_feed.py`

- [ ] **Step 1: Create base feed class**

Create `backend/app/services/external_feeds/base.py`:

```python
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

    async def get(self, cache_key: str, **kwargs) -> Any:
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
    async def fetch(self, **kwargs) -> Any:
        pass

    def fallback(self, **kwargs) -> Any:
        return {}

    async def close(self):
        await self._client.aclose()
```

- [ ] **Step 2: Create freight rate feed**

Create `backend/app/services/external_feeds/freight_feed.py`:

```python
"""
Freight rate feed — fetches current shipping cost data.

Production: Integrate with Freightos/Xeneta API.
Development: Returns realistic simulated rates based on route distance.
"""
import random
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed


class FreightRateFeed(ExternalFeed):
    """Freight rate data provider."""

    BASE_URL = "https://api.freightos.com/v1"  # placeholder

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=240)

    async def get_route_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        cache_key = f"freight:{origin}:{destination}:{int(weight_kg)}"
        return await self.get(cache_key, origin=origin, destination=destination, weight_kg=weight_kg)

    async def fetch(self, origin: str = "", destination: str = "", weight_kg: float = 0, **kwargs) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.BASE_URL}/rates",
                params={"origin": origin, "dest": destination, "weight": weight_kg},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_rate(origin, destination, weight_kg)

    def fallback(self, **kwargs) -> dict[str, Any]:
        return self._simulate_rate(
            kwargs.get("origin", ""), kwargs.get("destination", ""), kwargs.get("weight_kg", 10000)
        )

    def _simulate_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        base_per_ton = 45 + random.uniform(-5, 15)
        fuel_surcharge_pct = 0.10 + random.uniform(0, 0.08)
        insurance_pct = 0.015 + random.uniform(0, 0.005)
        tons = weight_kg / 1000
        base_cost = base_per_ton * tons
        return {
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "base_rate_per_ton": round(base_per_ton, 2),
            "fuel_surcharge_pct": round(fuel_surcharge_pct, 4),
            "insurance_pct": round(insurance_pct, 4),
            "estimated_cost": round(base_cost * (1 + fuel_surcharge_pct), 2),
            "insurance_cost": round(base_cost * insurance_pct, 2),
            "currency": "USD",
            "source": "simulated",
            "valid_until": "2026-04-11",
        }


freight_feed = FreightRateFeed()
```

- [ ] **Step 3: Create geopolitical risk feed**

Create `backend/app/services/external_feeds/risk_feed.py`:

```python
"""
Geopolitical risk feed — fetches zone risk levels and active threats.

Production: Integrate with GDELT, ACLED, or ReliefWeb API.
Development: Returns simulated risk data updated daily.
"""
import random
from datetime import datetime
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed

ZONE_RISK_PROFILES = {
    "ZONE-001": {"base_risk": 8, "name": "Strait of Hormuz"},
    "ZONE-002": {"base_risk": 5, "name": "Suez Canal"},
    "ZONE-003": {"base_risk": 3, "name": "East China Sea / Japan"},
    "ZONE-004": {"base_risk": 6, "name": "South China Sea"},
    "ZONE-005": {"base_risk": 7, "name": "Black Sea / Russia"},
}


class GeopoliticalRiskFeed(ExternalFeed):
    """Geopolitical risk data provider."""

    GDELT_URL = "https://api.gdeltproject.org/api/v2"  # placeholder

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=360)

    async def get_zone_risk(self, zone_id: str) -> dict[str, Any]:
        return await self.get(f"risk:{zone_id}", zone_id=zone_id)

    async def get_all_zone_risks(self) -> list[dict[str, Any]]:
        results = []
        for zone_id in ZONE_RISK_PROFILES:
            results.append(await self.get_zone_risk(zone_id))
        return results

    async def fetch(self, zone_id: str = "", **kwargs) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.GDELT_URL}/context",
                params={"zone": zone_id},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_risk(zone_id)

    def fallback(self, **kwargs) -> dict[str, Any]:
        return self._simulate_risk(kwargs.get("zone_id", "ZONE-001"))

    def _simulate_risk(self, zone_id: str) -> dict[str, Any]:
        profile = ZONE_RISK_PROFILES.get(zone_id, {"base_risk": 5, "name": "Unknown"})
        noise = random.uniform(-1, 1)
        risk_level = max(1, min(10, profile["base_risk"] + noise))
        return {
            "zone_id": zone_id,
            "zone_name": profile["name"],
            "risk_level": round(risk_level, 1),
            "trend": random.choice(["stable", "increasing", "decreasing"]),
            "active_threats": random.randint(0, 3),
            "insurance_multiplier": round(1.0 + (risk_level / 10) * 2, 2),
            "updated_at": datetime.utcnow().isoformat(),
            "source": "simulated",
        }


risk_feed = GeopoliticalRiskFeed()
```

- [ ] **Step 4: Create sanctions feed**

Create `backend/app/services/external_feeds/sanctions_feed.py`:

```python
"""
Sanctions screening feed — checks entities against sanctions lists.

Production: Integrate with OpenSanctions API or OFAC SDN list.
Development: Returns simulated screening results.
"""
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed

KNOWN_SANCTIONED = {"Russia", "Iran", "North Korea", "Syria", "Belarus"}


class SanctionsFeed(ExternalFeed):
    """Sanctions screening provider."""

    OPENSANCTIONS_URL = "https://api.opensanctions.org/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=1440)  # 24h cache

    async def screen_entity(self, name: str, country: str) -> dict[str, Any]:
        return await self.get(f"sanctions:{name}:{country}", name=name, country=country)

    async def fetch(self, name: str = "", country: str = "", **kwargs) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.OPENSANCTIONS_URL}/match",
                params={"name": name, "country": country},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_screening(name, country)

    def fallback(self, **kwargs) -> dict[str, Any]:
        return {"name": kwargs.get("name", ""), "sanctioned": False, "source": "fallback"}

    def _simulate_screening(self, name: str, country: str) -> dict[str, Any]:
        is_sanctioned = country in KNOWN_SANCTIONED
        return {
            "name": name,
            "country": country,
            "sanctioned": is_sanctioned,
            "lists_matched": ["OFAC-SDN", "EU-CONSOLIDATED"] if is_sanctioned else [],
            "confidence": 0.95 if is_sanctioned else 0.0,
            "source": "simulated",
        }


sanctions_feed = SanctionsFeed()
```

- [ ] **Step 5: Create __init__.py for the package**

Create `backend/app/services/external_feeds/__init__.py`:

```python
from app.services.external_feeds.freight_feed import freight_feed
from app.services.external_feeds.risk_feed import risk_feed
from app.services.external_feeds.sanctions_feed import sanctions_feed

__all__ = ["freight_feed", "risk_feed", "sanctions_feed"]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/external_feeds/
git commit -m "feat: external data feed framework — freight rates, geopolitical risk, sanctions screening"
```

---

### Task 3.2: Feed API Router

**Files:**
- Create: `backend/app/routers/feeds.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Create feeds router**

Create `backend/app/routers/feeds.py`:

```python
from fastapi import APIRouter, Query

from app.services.external_feeds import freight_feed, risk_feed, sanctions_feed

router = APIRouter(prefix="/api/feeds", tags=["external-feeds"])


@router.get("/freight/rate")
async def get_freight_rate(
    origin: str = Query(...),
    destination: str = Query(...),
    weight_kg: float = Query(..., gt=0),
):
    """Get current freight rate for a route."""
    return await freight_feed.get_route_rate(origin, destination, weight_kg)


@router.get("/risk/zone/{zone_id}")
async def get_zone_risk(zone_id: str):
    """Get current geopolitical risk assessment for a zone."""
    return await risk_feed.get_zone_risk(zone_id)


@router.get("/risk/zones")
async def get_all_zone_risks():
    """Get risk assessments for all monitored zones."""
    return await risk_feed.get_all_zone_risks()


@router.get("/sanctions/screen")
async def screen_entity(
    name: str = Query(...),
    country: str = Query(...),
):
    """Screen an entity against sanctions lists."""
    return await sanctions_feed.screen_entity(name, country)
```

- [ ] **Step 2: Register router in main.py**

In `backend/app/main.py`, add:

```python
from app.routers.feeds import router as feeds_router
```

And:

```python
app.include_router(feeds_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/feeds.py backend/app/main.py
git commit -m "feat: add /api/feeds endpoints for freight rates, risk, and sanctions"
```

---

## Phase 4: Google Cloud Production Deployment

### Scope
Deploy the platform to Google Cloud using Cloud Run (backend), Cloud SQL (PostgreSQL), Memorystore (Redis), and a managed Neo4j instance. Use Terraform or gcloud CLI for infrastructure.

---

### Task 4.1: Dockerize Backend

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

- [ ] **Step 1: Create backend Dockerfile**

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

- [ ] **Step 2: Create .dockerignore**

Create `backend/.dockerignore`:

```
__pycache__
*.pyc
.pytest_cache
tests/
alembic/versions/__pycache__
.env
```

- [ ] **Step 3: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore
git commit -m "feat: add backend Dockerfile for Cloud Run deployment"
```

---

### Task 4.2: Dockerize Frontend

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

- [ ] **Step 1: Create frontend Dockerfile**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || npm ci

COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

- [ ] **Step 2: Create .dockerignore**

Create `frontend/.dockerignore`:

```
node_modules
.next
.git
```

- [ ] **Step 3: Commit**

```bash
git add frontend/Dockerfile frontend/.dockerignore
git commit -m "feat: add frontend Dockerfile for Cloud Run deployment"
```

---

### Task 4.3: Google Cloud Infrastructure Script

**Files:**
- Create: `infra/deploy-gcp.sh`
- Create: `infra/cloud-run-backend.yaml`
- Create: `infra/cloud-run-frontend.yaml`

- [ ] **Step 1: Create deployment script**

Create `infra/deploy-gcp.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE_NAME="scm-risk"
DB_INSTANCE="${SERVICE_NAME}-pg"
REDIS_INSTANCE="${SERVICE_NAME}-redis"
NEO4J_VM="${SERVICE_NAME}-neo4j"

echo "=== SCM Risk Intelligence — GCP Deployment ==="
echo "Project: $PROJECT_ID | Region: $REGION"

# 1. Enable APIs
echo "[1/7] Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project="$PROJECT_ID"

# 2. Create Artifact Registry
echo "[2/7] Creating Artifact Registry..."
gcloud artifacts repositories create scm-risk \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || true

# 3. Cloud SQL (PostgreSQL)
echo "[3/7] Creating Cloud SQL instance..."
gcloud sql instances create "$DB_INSTANCE" \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --storage-auto-increase 2>/dev/null || echo "Instance exists"

gcloud sql databases create scm_risk_db \
  --instance="$DB_INSTANCE" \
  --project="$PROJECT_ID" 2>/dev/null || true

gcloud sql users create scmrisk \
  --instance="$DB_INSTANCE" \
  --password="$(openssl rand -base64 24)" \
  --project="$PROJECT_ID" 2>/dev/null || true

# 4. Memorystore (Redis)
echo "[4/7] Creating Memorystore Redis..."
gcloud redis instances create "$REDIS_INSTANCE" \
  --size=1 \
  --region="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || echo "Instance exists"

# 5. Build and push images
echo "[5/7] Building and pushing Docker images..."
REGISTRY="$REGION-docker.pkg.dev/$PROJECT_ID/scm-risk"

docker build -t "$REGISTRY/backend:latest" ./backend
docker push "$REGISTRY/backend:latest"

docker build -t "$REGISTRY/frontend:latest" ./frontend
docker push "$REGISTRY/frontend:latest"

# 6. Deploy backend to Cloud Run
echo "[6/7] Deploying backend..."
gcloud run deploy "${SERVICE_NAME}-api" \
  --image="$REGISTRY/backend:latest" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="NEO4J_URI=bolt://${NEO4J_VM}:7687,NEO4J_USER=neo4j" \
  --set-secrets="NEO4J_PASSWORD=neo4j-password:latest,ANTHROPIC_API_KEY=anthropic-key:latest,POSTGRES_PASSWORD=pg-password:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:$DB_INSTANCE"

BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}-api" --region="$REGION" --format="value(status.url)")

# 7. Deploy frontend to Cloud Run
echo "[7/7] Deploying frontend..."
gcloud run deploy "${SERVICE_NAME}-web" \
  --image="$REGISTRY/frontend:latest" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --port=3000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"

FRONTEND_URL=$(gcloud run services describe "${SERVICE_NAME}-web" --region="$REGION" --format="value(status.url)")

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/health"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x infra/deploy-gcp.sh
```

- [ ] **Step 3: Commit**

```bash
git add infra/
git commit -m "feat: Google Cloud deployment script — Cloud Run, Cloud SQL, Memorystore"
```

---

### Task 4.4: Environment & Secrets Configuration

**Files:**
- Create: `backend/.env.example`
- Create: `infra/secrets-setup.sh`

- [ ] **Step 1: Create .env.example**

Create `backend/.env.example`:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=scmrisk2024

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=scmrisk
POSTGRES_PASSWORD=scmrisk2024
POSTGRES_DB=scm_risk_db
SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://scmrisk:scmrisk2024@localhost:5432/scm_risk_db

# Redis
REDIS_URL=redis://localhost:6379/0

# AI
ANTHROPIC_API_KEY=sk-ant-...

# External Feeds (optional — falls back to simulated data)
FREIGHTOS_API_KEY=
GDELT_API_KEY=
OPENSANCTIONS_API_KEY=

# App
APP_ENV=development
LOG_LEVEL=INFO
```

- [ ] **Step 2: Create secrets setup script**

Create `infra/secrets-setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"

echo "Creating GCP secrets..."

# Create secrets (prompts for values)
for SECRET in neo4j-password pg-password anthropic-key freightos-key; do
  echo "Enter value for $SECRET:"
  read -s VALUE
  echo -n "$VALUE" | gcloud secrets create "$SECRET" \
    --data-file=- \
    --project="$PROJECT_ID" 2>/dev/null || \
  echo -n "$VALUE" | gcloud secrets versions add "$SECRET" \
    --data-file=- \
    --project="$PROJECT_ID"
  echo "  -> $SECRET stored"
done

echo "Done. Grant Cloud Run service account access with:"
echo "  gcloud secrets add-iam-policy-binding SECRET --member=serviceAccount:SA --role=roles/secretmanager.secretAccessor"
```

- [ ] **Step 3: Make executable and commit**

```bash
chmod +x infra/secrets-setup.sh
git add backend/.env.example infra/secrets-setup.sh
git commit -m "feat: add environment template and GCP secrets setup"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Hedging alternatives (route + supplier) — Task 2.2, 2.3
- [x] TCO baseline vs scenario comparison — Task 2.1, 2.4
- [x] Decision-ready report with charts — Task 2.4
- [x] Module-specific DB schemas — Task 1.2 (6 schemas: suppliers, routes, equipment, disruptions, tco, audit)
- [x] External data feed APIs — Task 3.1, 3.2 (freight, risk, sanctions)
- [x] Google Cloud production deployment — Task 4.1-4.4

**2. Placeholder scan:** No TBD, TODO, or "implement later" found.

**3. Type consistency:**
- `HedgingReport`, `HedgingScenario`, `TCOBreakdown` — consistent across types.ts, api.ts, and HedgingReportView.tsx
- `calculate_baseline_tco`, `calculate_scenario_tco`, `compare_tco` — consistent signatures across tco_engine.py and hedging_service.py
- PostgreSQL model field names match sync_pg.py Neo4j query aliases
