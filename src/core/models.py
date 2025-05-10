# src/core/models.py
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


# ---------- Leaf models -------------------------------------------------- #
class SourceRef(BaseModel):
    """A single source URL (or file path) we pulled content from."""
    url: str
    title: str | None = None


class Trend(BaseModel):
    text: str = Field(..., description="Short phrase naming the trend")
    sources: List[SourceRef]


class Company(BaseModel):
    name: str
    context: str | None = Field(
        default=None,
        description="One-line reason this company is relevant",
    )
    sources: List[SourceRef]


class WhitespaceOpportunity(BaseModel):
    description: str
    sources: List[SourceRef]


# ---------- Stage-2: extraction result for ONE document ------------------ #
class DocumentExtraction(BaseModel):
    """What the LLM returns for a single cleaned article/page."""
    doc_source: SourceRef
    trends: List[Trend] = []
    companies: List[Company] = []
    whitespace_opportunities: List[WhitespaceOpportunity] = []


# ---------- Stage-4: final aggregated answer ----------------------------- #
class ResearchReport(BaseModel):
    query: str
    trends: List[Trend]
    companies: List[Company]
    whitespace_opportunities: List[WhitespaceOpportunity]
