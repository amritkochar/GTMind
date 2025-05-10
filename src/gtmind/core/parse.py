from __future__ import annotations

import asyncio
import logging
from typing import List

import httpx
import trafilatura

from gtmind.core.models import SourceRef
from gtmind.core.settings import settings

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    pass


class CleanDocument(SourceRef):
    """SourceRef enriched with cleaned article text."""
    text: str


# ---------- private helpers ------------------------------------------------- #
async def _download(url: str, client: httpx.AsyncClient) -> str:
    """Fetch raw HTML (raises FetchError on HTTP failure)."""
    try:
        resp = await client.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc


def _clean_html(html: str) -> str | None:
    """Return readable text via trafilatura; None if nothing extracted."""
    return trafilatura.extract(html, include_comments=False, include_tables=False)


# ---------- public API ------------------------------------------------------ #
async def fetch_and_clean(source: SourceRef) -> CleanDocument | None:
    """Download a single URL and strip boilerplate; returns None on failure."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            html = await _download(source.url, client)
        except FetchError as e:
            logger.warning("%s", e)
            return None

    text = _clean_html(html)
    if not text:
        logger.warning("No extractable text for %s", source.url)
        return None

    return CleanDocument(url=source.url, title=source.title, text=text)


async def batch_fetch_clean(sources: List[SourceRef]) -> List[CleanDocument]:
    """Parallel fetch/clean with concurrency cap."""
    sem = asyncio.Semaphore(10)  # limit inflight requests

    async def _task(src: SourceRef):
        async with sem:
            return await fetch_and_clean(src)

    cleaned = await asyncio.gather(*(_task(s) for s in sources))
    return [doc for doc in cleaned if doc is not None]


def batch_fetch_clean_sync(sources: List[SourceRef]) -> List[CleanDocument]:
    """Sync wrapper, handy for CLI."""
    return asyncio.run(batch_fetch_clean(sources))
