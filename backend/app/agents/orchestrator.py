"""Main Orchestrator Agent for the SCM Risk Intelligence Platform.

Routes user queries to appropriate sub-agents, synthesizes responses,
and optionally uses Claude API for enhanced natural language responses.
Falls back to rule-based routing when Claude API is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from app.agents.ai_client import get_client as get_anthropic_client
from app.config import settings
from app.agents.impact_agent import ImpactAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.route_agent import RouteAgent
from app.agents.cost_agent import CostAgent
from app.agents.news_agent import NewsAgent
from app.agents.disruption_agent import DisruptionAgent
from app.agents.tools.neo4j_tools import (
    find_affected_equipment,
    find_alternative_routes,
    find_alternative_suppliers,
    get_equipment_details,
    get_project_risk_summary,
    get_supplier_performance,
    query_neo4j,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the SCM Risk Intelligence AI, an expert assistant for supply chain
risk management in large-scale industrial projects (oil & gas, petrochemical, infrastructure).

You have access to a knowledge graph of projects, equipment, suppliers, shipping routes,
geopolitical zones, and disruption events. You help users:

1. Analyze the impact of supply chain disruptions
2. Find alternative suppliers and routes
3. Calculate costs and ROI of mitigation strategies
4. Monitor and detect emerging risks
5. Provide actionable recommendations

Always ground your analysis in data from the knowledge graph. When recommending actions,
consider criticality, cost, lead time, and certification requirements. Provide specific,
actionable recommendations with quantified impacts.

Available tools:
- analyze_impact: Analyze impact of a disruption on equipment, routes, and projects
- find_alternatives: Find alternative suppliers or routes for affected equipment
- calculate_costs: Calculate disruption costs and compare mitigation scenarios
- get_status: Get current status of projects, equipment, routes, or suppliers
- search_data: Query the supply chain knowledge graph directly
"""


class Orchestrator:
    """Main orchestrator that routes queries to appropriate agents."""

    def __init__(self) -> None:
        self.name = "Orchestrator"
        self.impact_agent = ImpactAgent()
        self.supplier_agent = SupplierAgent()
        self.route_agent = RouteAgent()
        self.cost_agent = CostAgent()
        self.news_agent = NewsAgent()
        self.disruption_agent = DisruptionAgent()
    def _get_anthropic_client(self):
        """Get shared Anthropic client."""
        return get_anthropic_client()

    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[str], Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query by routing to appropriate agents.

        Args:
            query: Natural language query from the user.
            context: Additional context (e.g., current disruption, selected project).
            callback: Optional streaming callback for progressive updates.

        Returns:
            Structured response with analysis results and natural language summary.
        """
        logger.info("Orchestrator.run: processing query: %s", query[:100])
        context = context or {}

        # Step 1: Classify intent and route to agents
        intent = self._classify_intent(query)

        if callback:
            await self._safe_callback(callback, f"Analyzing query... Intent: {intent['primary']}")

        # Step 2: Execute agent pipeline based on intent
        agent_results: Dict[str, Any] = {}

        try:
            if intent["primary"] == "impact_analysis":
                agent_results = await self._handle_impact_analysis(query, context, callback)
            elif intent["primary"] == "find_alternatives":
                agent_results = await self._handle_find_alternatives(query, context, callback)
            elif intent["primary"] == "cost_analysis":
                agent_results = await self._handle_cost_analysis(query, context, callback)
            elif intent["primary"] == "status_query":
                agent_results = await self._handle_status_query(query, context, callback)
            elif intent["primary"] == "disruption_detection":
                agent_results = await self._handle_disruption_detection(query, context, callback)
            else:
                agent_results = await self._handle_general_query(query, context, callback)
        except Exception as exc:
            logger.error("Agent execution failed: %s", exc)
            agent_results = {"error": str(exc)}

        # Step 3: Synthesize response (use Claude if available, else rule-based)
        response = await self._synthesize_response(query, intent, agent_results, callback)

        return response

    def _classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify the user's query intent using keyword analysis."""
        lower = query.lower()

        intent_keywords = {
            "impact_analysis": [
                "impact", "affect", "disruption", "damage", "risk", "threat",
                "what happens", "how does", "consequence", "cascade",
            ],
            "find_alternatives": [
                "alternative", "substitute", "replace", "backup", "other supplier",
                "other route", "reroute", "switch", "find another",
            ],
            "cost_analysis": [
                "cost", "price", "roi", "savings", "expense", "budget",
                "penalty", "liquidated damages", "overhead", "how much",
            ],
            "status_query": [
                "status", "current", "overview", "dashboard", "summary",
                "how is", "what is the state", "show me", "list",
            ],
            "disruption_detection": [
                "detect", "news", "alert", "monitor", "new event",
                "simulate", "scenario", "what if",
            ],
        }

        scores: Dict[str, int] = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in lower)
            scores[intent] = score

        primary = max(scores, key=scores.get) if any(scores.values()) else "general"
        if scores.get(primary, 0) == 0:
            primary = "general"

        return {
            "primary": primary,
            "scores": scores,
            "query": query,
        }

    async def _handle_impact_analysis(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle impact analysis queries."""
        if callback:
            await self._safe_callback(callback, "Running impact analysis...")

        # Check if we have a specific event in context
        event = context.get("event") or context.get("disruption")

        if not event:
            # Try to find active disruptions
            try:
                disruptions = await query_neo4j(
                    """
                    MATCH (d:DisruptionEvent)
                    WHERE d.verificationStatus <> 'resolved'
                    RETURN d {
                        .eventId, .type, .severity, .description,
                        .verificationStatus
                    } AS event
                    ORDER BY d.severity DESC
                    LIMIT 1
                    """
                )
                if disruptions:
                    event = disruptions[0].get("event")
            except Exception:
                pass

        if not event:
            # No active disruptions, return status
            return {
                "type": "impact_analysis",
                "message": "No active disruptions found. Use /simulate or provide an event to analyze.",
                "activeDisruptions": [],
            }

        zone_ids = event.get("affectedZones", [])
        impact = await self.impact_agent.run(event=event, affected_zone_ids=zone_ids)

        if callback:
            await self._safe_callback(
                callback,
                f"Impact analysis complete. {impact.get('affectedEquipmentCount', 0)} equipment items affected."
            )

        return {"type": "impact_analysis", "impact": impact}

    async def _handle_find_alternatives(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle alternative finding queries."""
        if callback:
            await self._safe_callback(callback, "Searching for alternatives...")

        lower = query.lower()
        results: Dict[str, Any] = {"type": "find_alternatives"}

        # Determine if looking for supplier or route alternatives
        if "supplier" in lower or "vendor" in lower:
            equipment = context.get("affectedEquipment", [])
            if not equipment:
                # Try to find at-risk equipment
                try:
                    records = await query_neo4j(
                        """
                        MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
                        WHERE r.currentStatus IN ['disrupted', 'blocked']
                        RETURN e {
                            .equipmentId, .name, .category, .criticality, .weight
                        } AS equipment
                        LIMIT 10
                        """
                    )
                    equipment = [r["equipment"] for r in records if r.get("equipment")]
                except Exception:
                    pass

            zone_ids = context.get("disruptedZoneIds", [])
            supplier_results = await self.supplier_agent.run(
                affected_equipment=equipment,
                disrupted_zone_ids=zone_ids,
            )
            results["supplierRecommendations"] = supplier_results

            if callback:
                await self._safe_callback(
                    callback,
                    f"Found alternatives for {supplier_results.get('equipmentWithAlternatives', 0)} equipment items."
                )

        if "route" in lower or "shipping" in lower or "reroute" in lower:
            blocked_routes = context.get("blockedRoutes", [])
            if not blocked_routes:
                try:
                    records = await query_neo4j(
                        """
                        MATCH (r:ShippingRoute)
                        WHERE r.currentStatus IN ['disrupted', 'blocked']
                        RETURN r {
                            .routeId, .name, .currentStatus,
                            .estimatedTransitDays, .shippingCost
                        } AS route
                        LIMIT 10
                        """
                    )
                    blocked_routes = [r["route"] for r in records if r.get("route")]
                except Exception:
                    pass

            equipment_list = context.get("equipment", [])
            zone_ids = context.get("disruptedZoneIds", [])
            route_results = await self.route_agent.run(
                blocked_routes=blocked_routes,
                equipment_list=equipment_list,
                disrupted_zone_ids=zone_ids,
            )
            results["routeRecommendations"] = route_results

            if callback:
                await self._safe_callback(
                    callback,
                    f"Route optimization complete. {route_results.get('routesWithAlternatives', 0)} routes with alternatives."
                )

        return results

    async def _handle_cost_analysis(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle cost analysis queries."""
        if callback:
            await self._safe_callback(callback, "Calculating costs...")

        projects = context.get("affectedProjects", [])
        equipment = context.get("affectedEquipment", [])
        delay_days = context.get("delayDays", 30)

        if not projects:
            try:
                records = await query_neo4j(
                    """
                    MATCH (p:Project)
                    WHERE p.status IN ['procurement', 'in_transit', 'construction']
                    RETURN p {
                        .projectId, .name, .totalValue, .status,
                        .criticalPathDeadline
                    } AS project
                    LIMIT 10
                    """
                )
                projects = [r["project"] for r in records if r.get("project")]
            except Exception:
                pass

        if not equipment:
            try:
                records = await query_neo4j(
                    """
                    MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
                    WHERE r.currentStatus IN ['disrupted', 'blocked']
                    RETURN e {
                        .equipmentId, .name, .criticality, .weight, .category
                    } AS equipment
                    LIMIT 20
                    """
                )
                equipment = [r["equipment"] for r in records if r.get("equipment")]
            except Exception:
                pass

        cost_results = await self.cost_agent.run(
            affected_projects=projects,
            affected_equipment=equipment,
            supplier_recommendations=context.get("supplierRecommendations"),
            route_recommendations=context.get("routeRecommendations"),
            delay_days=delay_days,
        )

        if callback:
            no_action = cost_results.get("noActionCost", {})
            await self._safe_callback(
                callback,
                f"Cost analysis complete. No-action cost: ${no_action.get('totalDisruptionCost', 0):,.0f}"
            )

        return {"type": "cost_analysis", "costs": cost_results}

    async def _handle_status_query(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle status/overview queries."""
        lower = query.lower()
        results: Dict[str, Any] = {"type": "status_query"}

        if callback:
            await self._safe_callback(callback, "Fetching current status...")

        # Check what kind of status is being requested
        if "project" in lower:
            project_id = context.get("projectId")
            if project_id:
                project = await get_project_risk_summary(project_id)
                results["project"] = project
            else:
                try:
                    records = await query_neo4j(
                        """
                        MATCH (p:Project)
                        RETURN p {
                            .projectId, .name, .status, .country,
                            .completionPct, .totalValue
                        } AS project
                        ORDER BY p.name LIMIT 20
                        """
                    )
                    results["projects"] = [r["project"] for r in records if r.get("project")]
                except Exception:
                    results["projects"] = []

        if "equipment" in lower:
            equipment_id = context.get("equipmentId")
            if equipment_id:
                equip = await get_equipment_details(equipment_id)
                results["equipment"] = equip
            else:
                try:
                    records = await query_neo4j(
                        """
                        MATCH (e:Equipment)
                        OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
                        RETURN e {
                            .equipmentId, .name, .category, .criticality,
                            routeStatus: r.currentStatus
                        } AS equipment
                        ORDER BY CASE e.criticality
                            WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                            WHEN 'medium' THEN 2 ELSE 3 END
                        LIMIT 20
                        """
                    )
                    results["equipmentList"] = [r["equipment"] for r in records if r.get("equipment")]
                except Exception:
                    results["equipmentList"] = []

        if "supplier" in lower:
            supplier_id = context.get("supplierId")
            if supplier_id:
                supplier = await get_supplier_performance(supplier_id)
                results["supplier"] = supplier
            else:
                try:
                    records = await query_neo4j(
                        """
                        MATCH (s:Supplier)
                        RETURN s {
                            .supplierId, .name, .country, .tier,
                            .onTimeDeliveryRate, .qualityRejectRate, .riskFlags
                        } AS supplier
                        ORDER BY s.name LIMIT 20
                        """
                    )
                    results["suppliers"] = [r["supplier"] for r in records if r.get("supplier")]
                except Exception:
                    results["suppliers"] = []

        if "route" in lower or "shipping" in lower:
            try:
                records = await query_neo4j(
                    """
                    MATCH (r:ShippingRoute)
                    RETURN r {
                        .routeId, .name, .currentStatus,
                        .estimatedTransitDays, .shippingCost
                    } AS route
                    ORDER BY CASE r.currentStatus
                        WHEN 'blocked' THEN 0 WHEN 'disrupted' THEN 1
                        WHEN 'delayed' THEN 2 ELSE 3 END
                    LIMIT 20
                    """
                )
                results["routes"] = [r["route"] for r in records if r.get("route")]
            except Exception:
                results["routes"] = []

        if "disruption" in lower or "risk" in lower:
            try:
                records = await query_neo4j(
                    """
                    MATCH (d:DisruptionEvent)
                    WHERE d.verificationStatus <> 'resolved'
                    RETURN d {
                        .eventId, .type, .severity, .description,
                        .verificationStatus
                    } AS disruption
                    ORDER BY d.severity DESC LIMIT 10
                    """
                )
                results["disruptions"] = [r["disruption"] for r in records if r.get("disruption")]
            except Exception:
                results["disruptions"] = []

        # If no specific entity requested, return overall dashboard
        if len(results) == 1:  # Only "type" key
            results.update(await self._get_dashboard())

        return results

    async def _handle_disruption_detection(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle disruption detection / simulation queries."""
        if callback:
            await self._safe_callback(callback, "Simulating disruption detection...")

        scenario_id = context.get("scenarioId")
        news_result = await self.news_agent.run(scenario_id=scenario_id)

        if callback:
            await self._safe_callback(
                callback,
                f"Detected: {news_result.get('eventCandidate', {}).get('headline', 'Unknown')}"
            )

        # Run disruption agent
        disruption_result = await self.disruption_agent.run(
            event_candidate=news_result["eventCandidate"],
            matched_zones=news_result.get("matchedZones", []),
            auto_trigger_impact=True,
        )

        return {
            "type": "disruption_detection",
            "newsDetection": news_result,
            "disruptionResult": disruption_result,
        }

    async def _handle_general_query(
        self,
        query: str,
        context: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Handle general queries with direct Neo4j lookups."""
        if callback:
            await self._safe_callback(callback, "Searching knowledge graph...")

        dashboard = await self._get_dashboard()
        return {"type": "general", **dashboard}

    async def _get_dashboard(self) -> Dict[str, Any]:
        """Get high-level dashboard data."""
        try:
            records = await query_neo4j(
                """
                OPTIONAL MATCH (p:Project)
                WITH count(p) AS totalProjects
                OPTIONAL MATCH (d:DisruptionEvent)
                WHERE d.verificationStatus <> 'resolved'
                WITH totalProjects, count(d) AS activeDisruptions,
                     collect(d {.eventId, .type, .severity, .description})[..5] AS topDisruptions
                OPTIONAL MATCH (r:ShippingRoute)
                WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
                WITH totalProjects, activeDisruptions, topDisruptions,
                     count(r) AS disruptedRoutes
                OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(rr:ShippingRoute)
                WHERE rr.currentStatus IN ['disrupted', 'blocked']
                RETURN {
                    totalProjects: totalProjects,
                    activeDisruptions: activeDisruptions,
                    disruptedRoutes: disruptedRoutes,
                    atRiskEquipment: count(DISTINCT e),
                    topDisruptions: topDisruptions
                } AS dashboard
                """
            )
            if records:
                return {"dashboard": records[0].get("dashboard", {})}
        except Exception as exc:
            logger.warning("Dashboard query failed: %s", exc)

        return {"dashboard": {}}

    async def _synthesize_response(
        self,
        query: str,
        intent: Dict[str, Any],
        agent_results: Dict[str, Any],
        callback: Optional[Callable],
    ) -> Dict[str, Any]:
        """Synthesize final response, using Claude API if available."""
        # Try Claude API for enhanced natural language response
        client = self._get_anthropic_client()
        nl_response = ""

        if client:
            try:
                results_text = json.dumps(agent_results, indent=2, default=str)[:8000]
                if callback:
                    # Streaming response
                    with client.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    f"Based on this analysis data:\n{results_text}\n\n"
                                    f"User query: {query}\n\n"
                                    "Provide a concise, actionable analysis with specific recommendations."
                                ),
                            }
                        ],
                    ) as stream:
                        chunks = []
                        for text in stream.text_stream:
                            chunks.append(text)
                            await self._safe_callback(callback, text)
                        nl_response = "".join(chunks)
                else:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    f"Based on this analysis data:\n{results_text}\n\n"
                                    f"User query: {query}\n\n"
                                    "Provide a concise, actionable analysis with specific recommendations."
                                ),
                            }
                        ],
                    )
                    nl_response = response.content[0].text
            except Exception as exc:
                logger.warning("Claude API call failed, using rule-based summary: %s", exc)
                nl_response = self._rule_based_summary(intent, agent_results)
        else:
            nl_response = self._rule_based_summary(intent, agent_results)

        return {
            "query": query,
            "intent": intent["primary"],
            "response": nl_response,
            "data": agent_results,
            "sources": list(agent_results.keys()),
            "enhancedByAI": bool(client and nl_response),
        }

    def _rule_based_summary(
        self, intent: Dict[str, Any], results: Dict[str, Any]
    ) -> str:
        """Generate a rule-based summary when Claude API is unavailable."""
        result_type = results.get("type", "general")
        lines = []

        if result_type == "impact_analysis":
            impact = results.get("impact", {})
            if impact:
                lines.append(impact.get("summary", "Impact analysis completed."))
            else:
                lines.append("No active disruptions found to analyze.")

        elif result_type == "find_alternatives":
            supplier_recs = results.get("supplierRecommendations", {})
            route_recs = results.get("routeRecommendations", {})
            if supplier_recs:
                lines.append(supplier_recs.get("summary", "Supplier analysis completed."))
            if route_recs:
                lines.append(route_recs.get("summary", "Route analysis completed."))
            if not supplier_recs and not route_recs:
                lines.append("No disrupted equipment or routes found for alternative analysis.")

        elif result_type == "cost_analysis":
            costs = results.get("costs", {})
            if costs:
                lines.append(costs.get("summary", "Cost analysis completed."))
            else:
                lines.append("Insufficient data for cost analysis.")

        elif result_type == "disruption_detection":
            dr = results.get("disruptionResult", {})
            if dr:
                lines.append(dr.get("summary", "Disruption detection completed."))
            else:
                lines.append("No disruption simulation results available.")

        elif result_type == "status_query":
            dashboard = results.get("dashboard", {})
            if dashboard:
                lines.append("Current SCM Risk Intelligence Status:")
                lines.append(f"  Projects: {dashboard.get('totalProjects', 'N/A')}")
                lines.append(f"  Active Disruptions: {dashboard.get('activeDisruptions', 'N/A')}")
                lines.append(f"  Disrupted Routes: {dashboard.get('disruptedRoutes', 'N/A')}")
                lines.append(f"  Equipment at Risk: {dashboard.get('atRiskEquipment', 'N/A')}")
            for key in ["projects", "equipmentList", "suppliers", "routes", "disruptions"]:
                items = results.get(key, [])
                if items:
                    lines.append(f"\n{key.replace('List', '').title()}: {len(items)} items found.")
        else:
            dashboard = results.get("dashboard", {})
            if dashboard:
                lines.append("SCM Risk Intelligence Platform Overview:")
                lines.append(json.dumps(dashboard, indent=2, default=str))
            else:
                lines.append("Query processed. Please refine your question for more specific results.")

        if results.get("error"):
            lines.append(f"\nNote: An error occurred during analysis: {results['error']}")

        lines.append(
            "\nNote: Connect an Anthropic API key for AI-powered natural language analysis."
        )
        return "\n".join(lines)

    @staticmethod
    async def _safe_callback(callback: Callable, message: str) -> None:
        """Safely execute callback, handling both sync and async."""
        try:
            import asyncio
            result = callback(message)
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:
            logger.warning("Callback failed: %s", exc)
