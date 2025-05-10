# tests/core/test_models.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from gtmind.core.models import ResearchReport, SourceRef, Trend


def test_report_roundtrip():
    report = ResearchReport(
        query="AI in retail",
        trends=[Trend(text="AI-driven demand forecasting",
                      sources=[SourceRef(url="https://example.com")])],
        companies=[],
        whitespace_opportunities=[],
    )
    raw = report.model_dump()
    assert raw["query"] == "AI in retail"
    assert raw["trends"][0]["text"].startswith("AI-driven")
