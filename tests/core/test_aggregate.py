from gtmind.core.aggregate import aggregate
from gtmind.core.models import (
    DocumentExtraction,
    Trend,
    Company,
    WhitespaceOpportunity,
    SourceRef,
)


def _doc(url: str, trend: str, company: str, gap: str) -> DocumentExtraction:
    src = SourceRef(url=url, title="")
    return DocumentExtraction(
        doc_source=src,
        trends=[Trend(text=trend, sources=[src])],
        companies=[Company(name=company, context="", sources=[src])],
        whitespace_opportunities=[WhitespaceOpportunity(description=gap, sources=[src])],
    )


def test_aggregate_dedupes_and_ranks():
    docs = [
        _doc("u1", "AI demand forecasting", "ForecastPro", "Tier-2 retailers lack AI"),
        _doc("u2", "AI-driven demand forecasting", "ForecastPro", "Tier-2 retailers lack AI"),
        _doc("u3", "Shelf monitoring with CV", "ShelfSense", "Last-mile data gaps"),
    ]

    report = aggregate("AI in retail", docs)

    # Should merge similar trends and gaps (two vs. one)
    assert len(report.trends) == 2
    assert report.trends[0].text.lower().startswith("ai")
    # Companies deduped by exact name
    assert len(report.companies) == 2
    # Frequency ranking: ForecastPro first
    assert report.companies[0].name == "ForecastPro"
