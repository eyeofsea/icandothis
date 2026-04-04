import pytest
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
