from fastapi import APIRouter, Query
from typing import List

from app.services.external_feeds import freight_feed, risk_feed, sanctions_feed
from app.agents.news_agent import NewsAgent

router = APIRouter(prefix="/api/feeds", tags=["external-feeds"])

_news_agent = NewsAgent()


@router.get("/freight/rate")
async def get_freight_rate(
    origin: str = Query(...),
    destination: str = Query(...),
    weight_kg: float = Query(..., gt=0),
):
    """Get current freight rate for a route (fuel-price adjusted)."""
    return await freight_feed.get_route_rate(origin, destination, weight_kg)


@router.get("/risk/zone/{zone_id}")
async def get_zone_risk(zone_id: str):
    """Get current geopolitical risk assessment for a zone (via GDELT)."""
    return await risk_feed.get_zone_risk(zone_id)


@router.get("/risk/zones")
async def get_all_zone_risks():
    """Get risk assessments for all monitored zones (via GDELT)."""
    return await risk_feed.get_all_zone_risks()


@router.get("/sanctions/screen")
async def screen_entity(
    name: str = Query(...),
    country: str = Query(""),
):
    """Screen an entity against sanctions lists (via OpenSanctions)."""
    return await sanctions_feed.screen_entity(name, country)


@router.post("/sanctions/screen-bulk")
async def screen_entities_bulk(entities: List[dict]):
    """Screen multiple entities against sanctions lists."""
    return await sanctions_feed.screen_bulk(entities)


@router.get("/news/live")
async def get_live_news(
    query: str = Query(None, description="Custom search query"),
):
    """Get live supply chain disruption news from GDELT."""
    return await _news_agent.run(query=query)


@router.get("/news/feed")
async def get_news_feed(
    max_results: int = Query(5, ge=1, le=20),
):
    """Get multiple live news events across supply chain categories."""
    return await _news_agent.fetch_multiple(max_results=max_results)
