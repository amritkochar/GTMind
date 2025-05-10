import httpx
import respx
import pytest
from textwrap import dedent

from gtmind.core.models import SourceRef
from gtmind.core.parse import fetch_and_clean, CleanDocument

FAKE_HTML = dedent(
    """
    <html>
      <head><title>Demo</title></head>
      <body>
        <nav>Site nav</nav>
        <article>
          <h1>Amazing AI Retail Trend</h1>
          <p>Computer-vision shelf monitoring is growing fast.</p>
        </article>
        <footer>ads &amp; cookies</footer>
      </body>
    </html>
    """
)

@respx.mock
@pytest.mark.asyncio
async def test_fetch_and_clean_extracts_text(monkeypatch):
    url = "https://example.com/demo"
    respx.get(url).mock(return_value=httpx.Response(200, text=FAKE_HTML))

    doc = await fetch_and_clean(SourceRef(url=url, title="Demo"))
    assert isinstance(doc, CleanDocument)
    assert "shelf monitoring" in doc.text.lower()
    assert doc.title == "Demo"
