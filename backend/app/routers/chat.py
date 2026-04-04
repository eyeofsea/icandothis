import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.config import settings
from app.database.neo4j_client import get_neo4j

router = APIRouter(prefix="/api/agents", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    context: dict | None = None


class ChatResponse(BaseModel):
    reply: str
    data: dict | None = None
    sources: list[str] = []


SYSTEM_PROMPT = """You are an AI assistant for an SCM Risk Intelligence Platform.
You help users analyze supply chain risks, equipment status, shipping route disruptions,
and supplier performance. You have access to the supply chain knowledge graph.
Always provide actionable insights based on the data available."""


async def _build_context(message: str) -> dict:
    """Query Neo4j to build context relevant to the user's message."""
    db = await get_neo4j()
    context: dict = {"projects": [], "disruptions": [], "atRiskEquipment": []}

    lower = message.lower()

    if any(kw in lower for kw in ["project", "portfolio", "status", "overview"]):
        query = """
        MATCH (p:Project)
        RETURN p {.projectId, .name, .status, .country, .completionPct, .totalValue}
            AS project
        ORDER BY p.name LIMIT 10
        """
        records = await db.execute_read(query)
        context["projects"] = [r["project"] for r in records]

    if any(kw in lower for kw in ["disruption", "risk", "threat", "event", "crisis"]):
        query = """
        MATCH (d:DisruptionEvent)
        WHERE d.verificationStatus <> 'resolved'
        RETURN d {.eventId, .type, .severity, .description, .verificationStatus}
            AS disruption
        ORDER BY d.severity DESC LIMIT 10
        """
        records = await db.execute_read(query)
        context["disruptions"] = [r["disruption"] for r in records]

    if any(kw in lower for kw in ["equipment", "at risk", "critical", "delay"]):
        query = """
        MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
        WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
        OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
        RETURN e {
            .equipmentId, .name, .criticality,
            routeStatus: r.currentStatus,
            project: p.name
        } AS equipment
        ORDER BY CASE e.criticality
            WHEN 'critical' THEN 0 WHEN 'high' THEN 1
            WHEN 'medium' THEN 2 ELSE 3 END
        LIMIT 10
        """
        records = await db.execute_read(query)
        context["atRiskEquipment"] = [r["equipment"] for r in records]

    if any(kw in lower for kw in ["supplier", "vendor", "source"]):
        query = """
        MATCH (s:Supplier)
        WHERE size(s.riskFlags) > 0 OR s.onTimeDeliveryRate < 80
        RETURN s {.supplierId, .name, .country, .onTimeDeliveryRate,
                  .qualityRejectRate, .riskFlags} AS supplier
        ORDER BY s.onTimeDeliveryRate ASC LIMIT 10
        """
        records = await db.execute_read(query)
        context["flaggedSuppliers"] = [r["supplier"] for r in records]

    if any(kw in lower for kw in ["route", "shipping", "transit", "blocked"]):
        query = """
        MATCH (r:ShippingRoute)
        WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
        RETURN r {.routeId, .name, .currentStatus, .estimatedTransitDays,
                  .shippingCost} AS route
        ORDER BY CASE r.currentStatus
            WHEN 'blocked' THEN 0 WHEN 'disrupted' THEN 1 ELSE 2 END
        LIMIT 10
        """
        records = await db.execute_read(query)
        context["disruptedRoutes"] = [r["route"] for r in records]

    if any(kw in lower for kw in ["dashboard", "summary", "kpi", "overall"]):
        query = """
        OPTIONAL MATCH (p:Project)
        WITH count(p) AS totalProjects
        OPTIONAL MATCH (d:DisruptionEvent)
        WHERE d.verificationStatus <> 'resolved'
        WITH totalProjects, count(d) AS activeDisruptions
        OPTIONAL MATCH (r:ShippingRoute)
        WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
        RETURN {
            totalProjects: totalProjects,
            activeDisruptions: activeDisruptions,
            disruptedRoutes: count(r)
        } AS kpi
        """
        records = await db.execute_read(query)
        if records:
            context["kpi"] = records[0]["kpi"]

    return context


def _format_context(context: dict) -> str:
    """Format context dict into a readable string for the AI prompt."""
    parts = []
    if context.get("projects"):
        parts.append("Active projects:\n" + json.dumps(context["projects"], indent=2, default=str))
    if context.get("disruptions"):
        parts.append("Active disruptions:\n" + json.dumps(context["disruptions"], indent=2, default=str))
    if context.get("atRiskEquipment"):
        parts.append("At-risk equipment:\n" + json.dumps(context["atRiskEquipment"], indent=2, default=str))
    if context.get("flaggedSuppliers"):
        parts.append("Flagged suppliers:\n" + json.dumps(context["flaggedSuppliers"], indent=2, default=str))
    if context.get("disruptedRoutes"):
        parts.append("Disrupted routes:\n" + json.dumps(context["disruptedRoutes"], indent=2, default=str))
    if context.get("kpi"):
        parts.append("KPI summary:\n" + json.dumps(context["kpi"], indent=2, default=str))
    return "\n\n".join(parts) if parts else "No specific data found in the knowledge graph."


async def _generate_reply(message: str, context: dict) -> ChatResponse:
    """Generate an AI reply. Uses Anthropic API if key is set, otherwise returns context-based response."""
    context_text = _format_context(context)
    sources = [k for k, v in context.items() if v]

    if settings.ANTHROPIC_API_KEY:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context from the supply chain knowledge graph:\n{context_text}\n\nUser question: {message}",
                }
            ],
        )
        reply_text = response.content[0].text
    else:
        reply_text = (
            f"Based on the current supply chain data:\n\n{context_text}\n\n"
            "Note: Connect an Anthropic API key for AI-powered analysis."
        )

    return ChatResponse(reply=reply_text, data=context, sources=sources)


@router.post("/chat", response_model=ChatResponse)
async def chat(msg: ChatMessage):
    context = await _build_context(msg.message)
    if msg.context:
        context.update(msg.context)
    return await _generate_reply(msg.message, context)


@router.websocket("/chat/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = payload.get("message", data)
            except json.JSONDecodeError:
                message = data

            context = await _build_context(message)

            if settings.ANTHROPIC_API_KEY:
                import anthropic

                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                context_text = _format_context(context)

                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Context:\n{context_text}\n\nUser question: {message}",
                        }
                    ],
                ) as stream:
                    for text in stream.text_stream:
                        await websocket.send_json({"type": "stream", "content": text})

                await websocket.send_json({"type": "end", "data": context})
            else:
                context_text = _format_context(context)
                reply = (
                    f"Based on the current supply chain data:\n\n{context_text}\n\n"
                    "Note: Connect an Anthropic API key for AI-powered streaming."
                )
                for i in range(0, len(reply), 50):
                    await websocket.send_json({"type": "stream", "content": reply[i : i + 50]})
                await websocket.send_json({"type": "end", "data": context})

    except WebSocketDisconnect:
        pass
