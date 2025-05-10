import os

import pytest

from gtmind.api.run import _pipeline


@pytest.mark.skipif(
    not (os.getenv("SEARCH_API_KEY") and os.getenv("OPENAI_API_KEY")),
    reason="needs real API keys",
)
def test_pipeline_live_smoke():
    report = _pipeline("AI in fashion")
    assert report.trends  # should have at least 1 trend
