from __future__ import annotations

import itertools
import logging

from rapidfuzz import fuzz, process

from gtmind.core.models import (
    Company,
    DocumentExtraction,
    ResearchReport,
    SourceRef,
    Trend,
    WhitespaceOpportunity,
)

logger = logging.getLogger(__name__)

# --------------------------- helpers ------------------------------------ #


def _dedupe_strings(
    texts: list[tuple[str, SourceRef]], threshold: int = 75
) -> dict[str, list[SourceRef]]:
    """
    Collapse near-duplicate strings using RapidFuzz token-sort ratio.
    Returns {canonical_text: [sources]}.
    """
    buckets: dict[str, list[SourceRef]] = {}

    for text, src in texts:
        text_norm = text.lower()

        match = process.extractOne(
            text_norm,
            buckets.keys(),
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        key = match[0] if match else text
        buckets.setdefault(key, []).append(src)

    return buckets



def _merge_company_context(
    companies: list[tuple[str, SourceRef]]
) -> tuple[dict[str, list[SourceRef]], dict[str, str]]:
    """
    Dedupe companies by lowercased name, but preserve original casing separately.
    Returns: (buckets, display_names)
    """
    buckets: dict[str, list[SourceRef]] = {}
    display_names: dict[str, str] = {}

    for name, src in companies:
        key = name.lower()
        if key not in buckets:
            display_names[key] = name  # preserve original case
            buckets[key] = [src]
        else:
            buckets[key].append(src)

    return buckets, display_names


# --------------------------- public API ---------------------------------- #


def aggregate(query: str, docs: list[DocumentExtraction]) -> ResearchReport:
    """Combine multiple extractions into one ResearchReport."""
    # --- collect raw tuples -------------------------------------------------
    trend_pairs: list[tuple[str, SourceRef]] = list(
        itertools.chain.from_iterable(
            [(t.text, src) for t in d.trends for src in t.sources] for d in docs
        )
    )
    company_pairs: list[tuple[str, SourceRef]] = list(
        itertools.chain.from_iterable(
            [(c.name, src) for c in d.companies for src in c.sources] for d in docs
        )
    )
    gap_pairs: list[tuple[str, SourceRef]] = list(
        itertools.chain.from_iterable(
            [(w.description, src) for w in d.whitespace_opportunities for src in w.sources]
            for d in docs
        )
    )

    # --- dedupe -------------------------------------------------------------
    trend_buckets = _dedupe_strings(trend_pairs)
    gap_buckets = _dedupe_strings(gap_pairs)
    company_buckets, display_names = _merge_company_context(company_pairs)

    # --- rank by frequency --------------------------------------------------
    def _bucket_to_trend(text: str, sources: list[SourceRef]) -> Trend:
        return Trend(text=text, sources=sources)

    def _bucket_to_gap(text: str, sources: list[SourceRef]) -> WhitespaceOpportunity:
        return WhitespaceOpportunity(description=text, sources=sources)

    def _bucket_to_company(name: str, sources: list[SourceRef]) -> Company:
        return Company(name=name, context="", sources=sources)

    trends = sorted(
        (_bucket_to_trend(k, v) for k, v in trend_buckets.items()),
        key=lambda t: len(t.sources),
        reverse=True,
    )
    companies = sorted(
        (
            Company(name=display_names[k], context="", sources=v)
            for k, v in company_buckets.items()
        ),
        key=lambda c: len(c.sources),
        reverse=True,
    )
    gaps = sorted(
        (_bucket_to_gap(k, v) for k, v in gap_buckets.items()),
        key=lambda g: len(g.sources),
        reverse=True,
    )

    return ResearchReport(
        query=query,
        trends=trends,
        companies=companies,
        whitespace_opportunities=gaps,
    )
