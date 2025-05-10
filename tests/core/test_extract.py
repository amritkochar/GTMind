import asyncio
from pathlib import Path
from textwrap import dedent
import pytest

from gtmind.core.parse import CleanDocument
from gtmind.core.extract import extract_document

# --- stub CleanDocument ---
_DOC = CleanDocument(
    url="https://example.com",
    title="AI Demand Forecasting",
    text=dedent(
        """
        Retailers are adopting AI-driven demand forecasting to cut waste.
        Startups like ForecastPro and ShelfSense provide turnkey services.
        However, tier-2 regional chains still lack affordable solutions.
        """
    ),
)


@pytest.mark.asyncio
async def test_extract_document(monkeypatch):
    # --- monkeypatch OpenAI call ---
    async def _fake_call_llm(doc):
        return {
            "trends": ["AI-driven demand forecasting"],
            "companies": ["ForecastPro", "ShelfSense"],
            "whitespace_opportunities": ["Lack of solutions for tier-2 retailers"],
        }

    from gtmind.core import extract as mod

    monkeypatch.setattr(mod, "_call_llm", _fake_call_llm)

    result = await extract_document(_DOC)
    assert result is not None
    assert result.trends[0].text.startswith("AI-driven")
    assert result.companies[0].name == "ForecastPro"
