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
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100))
    category = Column(String(50))
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
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)
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
    source = Column(String(50))

    route = relationship("RouteRecord", back_populates="cost_history")


# ── equipment schema ──────────────────────────────────────────────

class EquipmentRegistry(Base):
    __tablename__ = "equipment_registry"
    __table_args__ = {"schema": "equipment"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)
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
    event_type = Column(String(50))
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
    neo4j_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    affected_zone_ids = Column(ARRAY(String), default=[])
    source = Column(String(100))
    raw_data = Column(JSONB)
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
    impact_score = Column(Float)
    details = Column(JSONB)

    disruption = relationship("DisruptionRecord", back_populates="impact_snapshots")


# ── tco schema ────────────────────────────────────────────────────

class TCOReport(Base):
    __tablename__ = "tco_reports"
    __table_args__ = {"schema": "tco"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disruption_id = Column(UUID(as_uuid=True), ForeignKey("disruptions.disruption_records.id"), nullable=True)
    title = Column(String(300), nullable=False)
    created_by = Column(String(100), default="system")
    status = Column(String(20), default="draft")
    baseline_tco = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    scenarios = relationship("TCOScenario", back_populates="report")


class TCOScenario(Base):
    __tablename__ = "tco_scenarios"
    __table_args__ = {"schema": "tco"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("tco.tco_reports.id"), nullable=False)
    scenario_type = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    alternative_route_id = Column(String(20))
    alternative_supplier_id = Column(String(20))
    affected_equipment_ids = Column(ARRAY(String), default=[])
    implementation_cost = Column(Numeric(15, 2), default=0)
    shipping_cost_delta = Column(Numeric(15, 2), default=0)
    insurance_cost_delta = Column(Numeric(15, 2), default=0)
    lead_time_delta_days = Column(Integer, default=0)
    delay_penalty_savings = Column(Numeric(15, 2), default=0)
    total_tco = Column(JSONB, nullable=False)
    tco_delta_vs_baseline = Column(Numeric(15, 2))
    risk_reduction_pct = Column(Float, default=0)
    net_savings = Column(Numeric(15, 2))
    benefit_cost_ratio = Column(Float)
    recommendation_rank = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    report = relationship("TCOReport", back_populates="scenarios")


# ── audit schema ──────────────────────────────────────────────────

class DecisionLog(Base):
    __tablename__ = "decision_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tco_report_id = Column(UUID(as_uuid=True), ForeignKey("tco.tco_reports.id"), nullable=True)
    decision_type = Column(String(50))
    decided_by = Column(String(100))
    scenario_id = Column(UUID(as_uuid=True), nullable=True)
    rationale = Column(Text)
    decided_at = Column(DateTime, server_default=func.now())


class ChangeLog(Base):
    __tablename__ = "change_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String(100), default="system")
    changed_at = Column(DateTime, server_default=func.now())
