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
