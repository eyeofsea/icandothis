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
                "event": {"eventId": "EVT-001", "severity": 5, "type": "geopolitical", "name": "Hormuz Blockade"},
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
