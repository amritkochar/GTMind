from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from gtmind.core.models import SourceRef
from gtmind.core.settings import settings

SERPER_URL = "https://google.serper.dev/search"
logger = logging.getLogger(__name__)


class SearchError(RuntimeError):
    pass


async def _fetch(query: str, client: httpx.AsyncClient) -> dict[str, Any]:
    """Low-level call to Serper.dev."""
    headers = {"X-API-KEY": settings.search_api_key}
    payload = {"q": query, "num": 10, "gl": "us"}
    resp = await client.post(SERPER_URL, json=payload, headers=headers, timeout=15)
    if resp.status_code >= 400:
        raise SearchError(f"Serper error {resp.status_code}: {resp.text[:200]}")
    return resp.json()


async def search(query: str) -> list[SourceRef]:
    """
    Perform a web search and return a list of SourceRef objects
    containing URL and title.  Uses Serper.dev; respects
    `settings.search_api_key`.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        data = await _fetch(query, client)

    # Serper returns 'organic' list with items: {title, link, snippet}
    hits = data.get("organic", [])[: settings.max_docs]
    results: list[SourceRef] = [
        SourceRef(url=hit["link"], title=hit.get("title")) for hit in hits
    ]
    if not results:
        logger.warning("No search results returned for query: %s", query)
    return results


# Synchronous helper for CLI / quick calls
def search_sync(query: str) -> list[SourceRef]:
    return asyncio.run(search(query))
