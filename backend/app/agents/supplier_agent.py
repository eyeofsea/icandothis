"""Supplier Recommendation Agent for the SCM Risk Intelligence Platform.

Takes affected equipment list, finds alternative suppliers via graph queries,
filters by certification/capacity/sanctions, and ranks alternatives using
multi-criteria scoring.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.tools.neo4j_tools import (
    find_alternative_suppliers,
    get_supplier_performance,
    query_neo4j,
)
from app.agents.tools.scoring import (
    calculate_supplier_risk_score,
    rank_alternatives,
)

logger = logging.getLogger(__name__)


class SupplierAgent:
    """Finds and ranks alternative suppliers for disrupted equipment."""

    def __init__(self) -> None:
        self.name = "SupplierAgent"

    async def run(
        self,
        affected_equipment: List[Dict[str, Any]],
        disrupted_zone_ids: Optional[List[str]] = None,
        required_certifications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find and rank alternative suppliers for affected equipment.

        Args:
            affected_equipment: List of equipment dicts with category, criticality, etc.
            disrupted_zone_ids: Zones to exclude suppliers from.
            required_certifications: Required supplier certifications.

        Returns:
            Structured recommendations with ranked alternatives per equipment.
        """
        logger.info("SupplierAgent.run: processing %d equipment items", len(affected_equipment))
        disrupted_zone_ids = disrupted_zone_ids or []

        recommendations: List[Dict[str, Any]] = []
        all_alternatives_count = 0

        # Group equipment by category to batch supplier lookups
        category_map: Dict[str, List[Dict[str, Any]]] = {}
        for eq in affected_equipment:
            cat = eq.get("category", "unknown")
            category_map.setdefault(cat, []).append(eq)

        # Find alternatives per category
        category_suppliers: Dict[str, List[Dict[str, Any]]] = {}
        for category in category_map:
            try:
                suppliers = await find_alternative_suppliers(
                    equipment_category=category,
                    excluded_zones=disrupted_zone_ids,
                    required_certifications=required_certifications,
                )
                category_suppliers[category] = suppliers
            except Exception as exc:
                logger.warning("Failed to find suppliers for category %s: %s", category, exc)
                category_suppliers[category] = []

        # Process each equipment item
        for eq in affected_equipment:
            category = eq.get("category", "unknown")
            candidates = category_suppliers.get(category, [])

            # Get current supplier info
            current_supplier = await self._get_current_supplier(eq.get("equipmentId"))

            # Score and rank alternatives
            scored_alternatives = self._score_alternatives(
                candidates, current_supplier, eq, required_certifications
            )

            # Rank using multi-criteria scoring
            ranked = rank_alternatives(scored_alternatives)

            all_alternatives_count += len(ranked)

            recommendations.append({
                "equipmentId": eq.get("equipmentId"),
                "equipmentName": eq.get("name"),
                "category": category,
                "criticality": eq.get("criticality"),
                "currentSupplier": current_supplier,
                "alternativeCount": len(ranked),
                "alternatives": ranked[:5],  # Top 5
                "bestAlternative": ranked[0] if ranked else None,
                "switchImpact": self._assess_switch_impact(
                    current_supplier, ranked[0] if ranked else None, eq
                ),
            })

        # Summary statistics
        equipment_with_alternatives = sum(1 for r in recommendations if r["alternativeCount"] > 0)
        equipment_without = sum(1 for r in recommendations if r["alternativeCount"] == 0)

        return {
            "recommendations": recommendations,
            "totalEquipmentProcessed": len(affected_equipment),
            "equipmentWithAlternatives": equipment_with_alternatives,
            "equipmentWithoutAlternatives": equipment_without,
            "totalAlternativesFound": all_alternatives_count,
            "excludedZones": disrupted_zone_ids,
            "summary": self._generate_summary(recommendations, disrupted_zone_ids),
        }

    async def _get_current_supplier(
        self, equipment_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get the current supplier for a piece of equipment."""
        if not equipment_id:
            return None
        try:
            cypher = """
            MATCH (s:Supplier)-[:SUPPLIES]->(e:Equipment {equipmentId: $equipmentId})
            RETURN s {
                .supplierId, .name, .country, .region, .tier,
                .capabilities, .certifications, .financialRating,
                .deliveryRate, .qualityRate, .leadTimeDays,
                .capacityUtilization, .riskFlags
            } AS supplier
            LIMIT 1
            """
            records = await query_neo4j(cypher, {"equipmentId": equipment_id})
            if records and records[0].get("supplier"):
                return records[0]["supplier"]
        except Exception as exc:
            logger.warning("Failed to get current supplier for %s: %s", equipment_id, exc)
        return None

    def _score_alternatives(
        self,
        candidates: List[Dict[str, Any]],
        current_supplier: Optional[Dict[str, Any]],
        equipment: Dict[str, Any],
        required_certifications: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score alternatives using multi-criteria formula:
        Score = 0.3*(1-costDelta) + 0.3*(1-leadTimeDelta/maxLT) + 0.2*qualityScore
                + 0.1*certMatch + 0.1*relationshipScore
        """
        if not candidates:
            return []

        current_lead_time = (current_supplier or {}).get("leadTimeDays") or 60
        current_cost_proxy = (current_supplier or {}).get("financialRating", 5.0)
        required_certs = set(required_certifications or [])

        scored = []
        max_lead_time = max(
            (c.get("leadTimeDays") or 90 for c in candidates), default=90
        )

        for candidate in candidates:
            # Filter out sanctioned suppliers
            risk_flags = candidate.get("riskFlags") or []
            if "sanctioned" in risk_flags:
                continue

            # Filter by capacity - skip if over 95% utilized
            capacity = candidate.get("capacityUtilization") or 0
            if capacity > 95:
                continue

            cand_lead_time = candidate.get("leadTimeDays") or 90
            cand_quality = (candidate.get("qualityRate") or 80) / 100.0
            cand_delivery = (candidate.get("deliveryRate") or 80) / 100.0
            cand_financial = (candidate.get("financialRating") or 5) / 10.0

            # Cost delta (using financial rating as proxy since actual cost varies)
            cost_delta = abs(cand_financial - current_cost_proxy / 10.0)

            # Lead time delta
            lead_time_delta = max(0, cand_lead_time - current_lead_time)

            # Certification match
            cand_certs = set(candidate.get("certifications") or [])
            if required_certs:
                cert_match = len(cand_certs & required_certs) / len(required_certs)
            else:
                cert_match = 0.8 if cand_certs else 0.3

            # Relationship score (based on tier and delivery history)
            tier_scores = {"tier_1": 0.9, "tier_2": 0.6, "tier_3": 0.3}
            tier = str(candidate.get("tier", "tier_2")).lower()
            relationship_score = tier_scores.get(tier, 0.5)

            # Risk score for the supplier
            supplier_risk = calculate_supplier_risk_score(candidate)

            scored.append({
                "supplierId": candidate.get("supplierId"),
                "supplierName": candidate.get("name"),
                "country": candidate.get("country"),
                "region": candidate.get("region"),
                "tier": candidate.get("tier"),
                "capabilities": candidate.get("capabilities"),
                "certifications": candidate.get("certifications"),
                "leadTimeDays": cand_lead_time,
                "deliveryRate": candidate.get("deliveryRate"),
                "qualityRate": candidate.get("qualityRate"),
                "financialRating": candidate.get("financialRating"),
                "capacityUtilization": capacity,
                "supplierRiskScore": supplier_risk,
                "costDelta": round(cost_delta, 4),
                "leadTimeDelta": lead_time_delta,
                "qualityScore": round(cand_quality, 4),
                "certMatch": round(cert_match, 4),
                "relationshipScore": round(relationship_score, 4),
            })

        return scored

    def _assess_switch_impact(
        self,
        current_supplier: Optional[Dict[str, Any]],
        best_alternative: Optional[Dict[str, Any]],
        equipment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess the impact of switching to the best alternative supplier."""
        if not best_alternative:
            return {
                "feasible": False,
                "reason": "No alternative suppliers available.",
                "costImpact": 0,
                "leadTimeImpact": 0,
            }

        current_lt = (current_supplier or {}).get("leadTimeDays") or 60
        alt_lt = best_alternative.get("leadTimeDays") or 90
        lt_delta = alt_lt - current_lt

        current_quality = (current_supplier or {}).get("qualityRate") or 90
        alt_quality = best_alternative.get("qualityRate") or 80
        quality_delta = alt_quality - current_quality

        # Estimated cost impact (rough: $5,000 per day of lead time delta for critical)
        criticality = str(equipment.get("criticality", "medium")).lower()
        daily_cost = {"critical": 5000, "high": 3000, "medium": 1500, "low": 500}
        cost_impact = lt_delta * daily_cost.get(criticality, 1500)

        # Qualification time (new supplier qualification)
        qualification_days = 14 if best_alternative.get("tier") == "tier_1" else 30

        return {
            "feasible": True,
            "leadTimeImpactDays": lt_delta,
            "qualityDelta": round(quality_delta, 1),
            "estimatedCostImpact": cost_impact,
            "qualificationDays": qualification_days,
            "totalAdditionalDays": max(0, lt_delta) + qualification_days,
            "recommendation": (
                "Recommended" if lt_delta <= 14 and quality_delta >= -5
                else "Acceptable" if lt_delta <= 30
                else "Last resort"
            ),
        }

    def _generate_summary(
        self,
        recommendations: List[Dict[str, Any]],
        disrupted_zone_ids: List[str],
    ) -> str:
        """Generate human-readable summary of supplier recommendations."""
        total = len(recommendations)
        with_alts = sum(1 for r in recommendations if r["alternativeCount"] > 0)
        critical_without = sum(
            1 for r in recommendations
            if r["alternativeCount"] == 0
            and str(r.get("criticality", "")).lower() == "critical"
        )

        lines = [
            f"SUPPLIER RECOMMENDATION SUMMARY",
            f"Equipment processed: {total}",
            f"With alternatives: {with_alts}",
            f"Without alternatives: {total - with_alts}",
        ]

        if critical_without > 0:
            lines.append(
                f"WARNING: {critical_without} critical equipment item(s) have no alternative suppliers."
            )

        if disrupted_zone_ids:
            lines.append(f"Excluded zones: {', '.join(disrupted_zone_ids)}")

        # Top recommendations
        feasible = [r for r in recommendations if r.get("bestAlternative")]
        if feasible:
            lines.append("")
            lines.append("Top Recommendations:")
            for rec in feasible[:5]:
                best = rec["bestAlternative"]
                impact = rec.get("switchImpact", {})
                lines.append(
                    f"  - {rec.get('equipmentName', 'Unknown')}: "
                    f"Switch to {best.get('supplierName', 'Unknown')} "
                    f"({best.get('country', '?')}), "
                    f"+{impact.get('totalAdditionalDays', 0)} days, "
                    f"${impact.get('estimatedCostImpact', 0):,.0f} cost impact"
                )

        return "\n".join(lines)
