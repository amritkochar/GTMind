from __future__ import annotations

import asyncio
import logging

import httpx
import trafilatura

from gtmind.core.models import SourceRef
from gtmind.core.settings import settings

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    pass


class CleanDocument(SourceRef):
    text: str


async def _download(url: str, client: httpx.AsyncClient) -> str:
    """Fetch raw HTML, raising FetchError on failure."""
    try:
        resp = await client.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GTMindBot/1.0)"}
        )
        # Raises HTTPStatusError on 4xx/5xx
        resp.raise_for_status()
        return resp.text

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in {401, 403}:
            logger.warning("Blocked by site (%s): %s", status, url)
        else:
            logger.warning("HTTP error %s fetching %s", status, url)
        raise FetchError(f"Failed to fetch {url}: HTTP {status}") from exc

    except httpx.TimeoutException as exc:
        logger.warning("Timeout fetching %s: %s", url, exc)
        raise FetchError(f"Timeout fetching {url}") from exc

    except httpx.HTTPError as exc:
        logger.warning("Network error fetching %s: %s", url, exc)
        raise FetchError(f"Network error fetching {url}: {exc}") from exc


def _clean_html(html: str) -> str | None:
    return trafilatura.extract(html, include_comments=False, include_tables=False)


async def fetch_and_clean(source: SourceRef) -> CleanDocument | None:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            html = await _download(source.url, client)
        except FetchError:
            return None

    text = _clean_html(html)
    if not text:
        logger.warning("No extractable text for %s", source.url)
        return None

    return CleanDocument(url=source.url, title=source.title, text=text)


async def batch_fetch_clean(sources: list[SourceRef]) -> list[CleanDocument]:
    if not sources:
        logger.warning("batch_fetch_clean() called with empty sources")
        return []

    sem = asyncio.Semaphore(settings.fetch_concurrency_limit)

    async def _task(src: SourceRef) -> CleanDocument | None:
        async with sem:
            return await fetch_and_clean(src)

    cleaned = await asyncio.gather(*(_task(s) for s in sources))
    return [doc for doc in cleaned if doc is not None]


def batch_fetch_clean_sync(sources: list[SourceRef]) -> list[CleanDocument]:
    return asyncio.run(batch_fetch_clean(sources))
