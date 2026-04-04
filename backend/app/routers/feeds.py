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
