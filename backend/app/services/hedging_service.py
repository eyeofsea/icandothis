"""
Orchestrates hedging alternatives and TCO comparison reports.
Pulls data from Neo4j, calculates TCO via tco_engine, persists to PostgreSQL.
"""
from typing import Any

from app.database.neo4j_client import Neo4jClient
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
        scenarios: list[dict[str, Any]] = []

        # Reroute scenarios
        for alt in alt_routes[:3]:
            additional_days = alt.get("additionalDays", 0)
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
        for alt in alt_suppliers[:3]:
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
        neo4j = await Neo4jClient.get_instance()

        # Fetch event
        event_q = """
        MATCH (d:DisruptionEvent {eventId: $eventId})
        OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
        RETURN d {.*} AS event, collect(z.zoneId) AS zoneIds
        """
        event_records = await neo4j.execute_read(event_q, {"eventId": disruption_id})
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
        equip_records = await neo4j.execute_read(equip_q, {"zoneIds": zone_ids})
        equipment = [r["equipment"] for r in equip_records]

        # Fetch affected routes
        route_q = """
        MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
        WHERE z.zoneId IN $zoneIds
        RETURN DISTINCT r {.*} AS route
        """
        route_records = await neo4j.execute_read(route_q, {"zoneIds": zone_ids})
        affected_routes = [r["route"] for r in route_records]

        # Fetch affected projects
        project_q = """
        MATCH (p:Project)-[:HAS_EQUIPMENT]->(e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
        WHERE z.zoneId IN $zoneIds
        RETURN DISTINCT p {.*} AS project
        """
        proj_records = await neo4j.execute_read(project_q, {"zoneIds": zone_ids})
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
        alt_route_records = await neo4j.execute_read(alt_route_q, {"zoneIds": zone_ids})
        alt_routes = [r["route"] for r in alt_route_records]

        # Find alternative suppliers (outside disrupted zones)
        categories = list({eq.get("category") for eq in equipment if eq.get("category")})
        alt_suppliers: list[dict[str, Any]] = []
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
            sup_records = await neo4j.execute_read(sup_q, {"category": cat, "zoneIds": zone_ids})
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
        event: dict[str, Any],
        baseline: dict[str, Any],
        best_scenario: dict[str, Any] | None,
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
