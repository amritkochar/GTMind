import json

import httpx
import pytest
import respx

from gtmind.core.models import SourceRef
from gtmind.core.search import search

SERPER_URL = "https://google.serper.dev/search"


@respx.mock
@pytest.mark.asyncio
async def test_search_parses_results(monkeypatch):
    # -- Arrange ----------------------------------------------------------------
    fake_payload = {
        "organic": [
            {"title": "AI Retail News", "link": "https://example.com/ai-retail"},
            {"title": "How AI helps stores", "link": "https://example.com/help"},
        ]
    }
    respx.post(SERPER_URL).mock(
        return_value=httpx.Response(200, json=fake_payload)
    )

    # Provide a dummy API key for this test
    monkeypatch.setenv("SEARCH_API_KEY", "dummy-key")

    # -- Act --------------------------------------------------------------------
    results = await search("AI in retail")

    # -- Assert -----------------------------------------------------------------
    assert all(isinstance(r, SourceRef) for r in results)
    assert results[0].url == "https://example.com/ai-retail"
    assert results[0].title == "AI Retail News"
    assert len(results) == 2
    
    # Pretty print the results for debugging purposes
    print(json.dumps([r.model_dump() for r in results], indent=4))
