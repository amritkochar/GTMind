from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

import httpx

from gtmind.core.models import SourceRef
from gtmind.core.settings import settings

SERPER_URL = "https://google.serper.dev/search"
logger = logging.getLogger(__name__)


class SearchError(RuntimeError):
    pass


async def _fetch(query: str, client: httpx.AsyncClient) -> dict[str, Any]:
    headers = {"X-API-KEY": settings.search_api_key}
    payload = {"q": query, "num": 10, "gl": "us"}
    resp = await client.post(SERPER_URL, json=payload, headers=headers, timeout=15)
    if resp.status_code >= 400:
        raise SearchError(f"Serper error {resp.status_code}: {resp.text[:200]}")
    data: Any = resp.json()
    return cast(dict[str, Any], data)


async def search(query: str) -> list[SourceRef]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        data = await _fetch(query, client)

    hits = data.get("organic", [])[: settings.max_docs]
    results = [SourceRef(url=h["link"], title=h.get("title")) for h in hits]
    if not results:
        logger.warning("No search results for %s", query)
    return results


def search_sync(query: str) -> list[SourceRef]:
    return asyncio.run(search(query))
