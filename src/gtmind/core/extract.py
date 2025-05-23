from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, cast

import openai
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from gtmind.core.models import (
    Company,
    DocumentExtraction,
    SourceRef,
    Trend,
    WhitespaceOpportunity,
)
from gtmind.core.parse import CleanDocument
from gtmind.core.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_TOOL_SCHEMA
from gtmind.core.settings import settings

logger = logging.getLogger(__name__)
_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


@retry(wait=wait_exponential_jitter(1, 10), stop=stop_after_attempt(4))
async def _call_llm(doc: CleanDocument) -> dict[str, Any]:
    logger.info("LLM extracting from %s", doc.url[:60])

    response = await _client.chat.completions.create(  # type: ignore[call-overload]
        model=settings.model,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": doc.text[:12_000]},
        ],
        tools=[EXTRACTION_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "extract_insights"}},
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    tool_args = response.choices[0].message.tool_calls[0].function.arguments
    return cast(dict[str, Any], json.loads(tool_args))


async def extract_document(doc: CleanDocument) -> DocumentExtraction | None:
    try:
        data = await _call_llm(doc)
    except Exception as e:
        logger.error("LLM failed for %s: %s", doc.url, e)
        return None

    source = SourceRef(url=doc.url, title=doc.title)

    return DocumentExtraction(
        doc_source=source,
        trends=[Trend(text=t, sources=[source]) for t in data["trends"][:3]],
        companies=[
            Company(name=c["name"], context=c["context"], sources=[source])
            for c in data["companies"]
        ],
        whitespace_opportunities=[
            WhitespaceOpportunity(description=w, sources=[source])
            for w in data["whitespace_opportunities"]
        ],
    )


async def batch_extract(docs: list[CleanDocument]) -> list[DocumentExtraction]:
    sem = asyncio.Semaphore(settings.extract_concurrency_limit)

    async def _task(d: CleanDocument) -> DocumentExtraction | None:
        async with sem:
            return await extract_document(d)

    out = await asyncio.gather(*(_task(d) for d in docs))
    return [d for d in out if d is not None]


def batch_extract_sync(docs: list[CleanDocument]) -> list[DocumentExtraction]:
    return asyncio.run(batch_extract(docs))
