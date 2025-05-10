from __future__ import annotations

import asyncio
import json
import logging

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
from gtmind.core.settings import settings

logger = logging.getLogger(__name__)

_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_insights",
        "description": "Pull key trends, companies and whitespace gaps from article text.",
        "parameters": {
            "type": "object",
            "properties": {
                "trends": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3,
                },
                "companies": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "whitespace_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["trends", "companies", "whitespace_opportunities"],
        },
    },
}

_SYSTEM_PROMPT = (
    "You are an industry research assistant. "
    "Given an article, extract:\n"
    "1. Up to three concise AI/tech trends discussed.\n"
    "2. Companies mentioned (with relevance context).\n"
    "3. Any problems or whitespace opportunities.\n"
    "Respond via the provided JSON schema only."
)


@retry(wait=wait_exponential_jitter(1, 10), stop=stop_after_attempt(4))
async def _call_llm(doc: CleanDocument) -> dict:
    """Call GPT-4o in JSON-mode, retrying on 5xx/429."""
    logger.info("LLM extracting from %s", doc.url[:60])

    response = await _client.chat.completions.create(
        model=settings.model,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "extract_insights"}},
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": doc.text[:12_000]},  # truncate large docs
        ],
        temperature=0.2,
    )

    tool_out = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(tool_out)


async def extract_document(doc: CleanDocument) -> DocumentExtraction | None:
    """Return DocumentExtraction or None if LLM fails."""
    try:
        data = await _call_llm(doc)
    except Exception as e:
        logger.error("LLM failed for %s: %s", doc.url, e)
        return None

    source = SourceRef(url=doc.url, title=doc.title)

    return DocumentExtraction(
        doc_source=source,
        trends=[Trend(text=t, sources=[source]) for t in data["trends"]],
        companies=[
            Company(name=c, context="", sources=[source]) for c in data["companies"]
        ],
        whitespace_opportunities=[
            WhitespaceOpportunity(description=w, sources=[source])
            for w in data["whitespace_opportunities"]
        ],
    )


async def batch_extract(docs: list[CleanDocument]) -> list[DocumentExtraction]:
    sem = asyncio.Semaphore(5)

    async def _task(d: CleanDocument):
        async with sem:
            return await extract_document(d)

    out = await asyncio.gather(*(_task(d) for d in docs))
    return [d for d in out if d is not None]


def batch_extract_sync(docs: list[CleanDocument]) -> list[DocumentExtraction]:
    return asyncio.run(batch_extract(docs))
