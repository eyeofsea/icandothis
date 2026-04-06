"""Shared AI client for agent-level Claude API integration.

Provides a lazy-initialized singleton Anthropic client and a helper
to call Claude with structured prompts. All agents share one client
instance to avoid redundant connections.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_anthropic_client = None
_init_attempted = False

MODEL = "claude-sonnet-4-20250514"


def get_client():
    """Get or create the shared Anthropic client. Returns None if no API key."""
    global _anthropic_client, _init_attempted
    if _anthropic_client is not None:
        return _anthropic_client
    if _init_attempted:
        return None
    _init_attempted = True

    if not settings.ANTHROPIC_API_KEY:
        return None

    try:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        logger.info("Shared Anthropic client initialized for agents")
        return _anthropic_client
    except Exception as exc:
        logger.warning("Failed to initialize Anthropic client: %s", exc)
        return None


async def ai_analyze(
    system_prompt: str,
    user_prompt: str,
    data: Optional[Dict[str, Any]] = None,
    max_tokens: int = 1024,
) -> Optional[str]:
    """Call Claude API for analysis. Returns None if unavailable.

    Args:
        system_prompt: System instructions for the agent persona.
        user_prompt: The specific analysis request.
        data: Optional structured data to include in the prompt.
        max_tokens: Max response tokens.

    Returns:
        Claude's response text, or None if API is unavailable.
    """
    client = get_client()
    if not client:
        return None

    try:
        content = user_prompt
        if data:
            data_str = json.dumps(data, indent=2, default=str)[:6000]
            content = f"{user_prompt}\n\nData:\n{data_str}"

        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        return response.content[0].text
    except Exception as exc:
        logger.warning("Claude API call failed: %s", exc)
        return None
