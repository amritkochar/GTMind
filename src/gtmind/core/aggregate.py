from __future__ import annotations

import itertools
import logging
import re
import unicodedata
from collections import defaultdict

from rapidfuzz import fuzz

from gtmind.core.models import (
    Company,
    DocumentExtraction,
    ResearchReport,
    SourceRef,
    Trend,
    WhitespaceOpportunity,
)
from gtmind.core.settings import settings

logger = logging.getLogger(__name__)

# ---------- normaliser helpers ------------------------------------------- #
_STOPWORDS = {
    "ai", "the", "a", "an", "of", "in", "on", "with", "for", "and", "to",
}
_punct_re = re.compile(r"[^\w\s]")
_ws_re = re.compile(r"\s+")


def _normalize(text: str) -> str:
    txt = unicodedata.normalize("NFKD", text)
    txt = _punct_re.sub(" ", txt)
    tokens = [t.lower().rstrip("s") for t in _ws_re.split(txt) if t]
    tokens = [t for t in tokens if t not in _STOPWORDS]
    return " ".join(tokens)


# ---------- fuzzy-dedupe -------------------------------------------------- #
def _dedupe_strings(
    texts: list[tuple[str, SourceRef]],
    threshold: int = int(settings.dedupe_threshold),
) -> dict[str, list[SourceRef]]:
    buckets: dict[str, list[SourceRef]] = {}
    norm_cache: dict[str, str] = {}

    for raw_text, src in texts:
        norm = _normalize(raw_text)
        best_key: str | None = None
        best_score: float = 0.0  # fuzz returns float

        for canon, canon_norm in norm_cache.items():
            score = fuzz.token_sort_ratio(norm, canon_norm)
            if score >= threshold and score > best_score:
                best_key, best_score = canon, score

        key = best_key or raw_text
        buckets.setdefault(key, []).append(src)
        norm_cache.setdefault(key, norm)

    return buckets


# --------------------------- public API ---------------------------------- #
def aggregate(query: str, docs: list[DocumentExtraction]) -> ResearchReport:
    """Combine multiple extractions into one ResearchReport."""
    # --- collect -----------------------------------------------------------
    trend_pairs = list(
        itertools.chain.from_iterable(
            [(t.text, src) for t in d.trends for src in t.sources] for d in docs
        )
    )
    gap_pairs = list(
        itertools.chain.from_iterable(
            [(w.description, src) for w in d.whitespace_opportunities for src in w.sources]
            for d in docs
        )
    )
    company_triples = list(
        itertools.chain.from_iterable(
            [(c.name, c.context or "", src) for c in d.companies for src in c.sources]
            for d in docs
        )
    )

    # --- de-dupe -----------------------------------------------------------
    trend_buckets = _dedupe_strings(trend_pairs)
    gap_buckets = _dedupe_strings(gap_pairs)

    context_map: dict[str, str] = {}
    company_buckets: dict[str, list[SourceRef]] = defaultdict(list)
    display_names: dict[str, str] = {}

    for name, context, src in company_triples:
        key = name.lower().strip()
        company_buckets[key].append(src)
        display_names[key] = name
        if key not in context_map and context:
            context_map[key] = context

    # --- builders ----------------------------------------------------------
    def _bucket_to_trend(text: str, sources: list[SourceRef]) -> Trend:
        uniq = list({s.url: s for s in sources}.values())
        return Trend(text=text, sources=uniq)

    def _bucket_to_gap(text: str, sources: list[SourceRef]) -> WhitespaceOpportunity:
        uniq = list({s.url: s for s in sources}.values())
        return WhitespaceOpportunity(description=text, sources=uniq)

    def _bucket_to_company(key: str, sources: list[SourceRef]) -> Company:
        uniq = list({s.url: s for s in sources}.values())
        return Company(
            name=display_names[key],
            context=context_map.get(key, ""),
            sources=uniq,
        )

    trends = sorted(
        (_bucket_to_trend(k, v) for k, v in trend_buckets.items()),
        key=lambda t: len(t.sources),
        reverse=True,
    )
    companies = sorted(
        (_bucket_to_company(k, v) for k, v in company_buckets.items()),
        key=lambda c: len(c.sources),
        reverse=True,
    )
    gaps = sorted(
        (_bucket_to_gap(k, v) for k, v in gap_buckets.items()),
        key=lambda g: len(g.sources),
        reverse=True,
    )

    for k, v in trend_buckets.items():
        logger.debug("%s appears in %d sources", k, len(v))

    return ResearchReport(
        query=query, trends=trends, companies=companies, whitespace_opportunities=gaps
    )
