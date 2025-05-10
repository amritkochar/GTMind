# src/core/models.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ---------- Leaf models -------------------------------------------------- #
class SourceRef(BaseModel):
    """A single source URL (or file path) we pulled content from."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str | None = None


class Trend(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Short phrase naming the trend")
    sources: list[SourceRef]


class Company(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    context: str | None = Field(
        default=None,
        description="One-line reason this company is relevant",
    )
    sources: list[SourceRef]


class WhitespaceOpportunity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    sources: list[SourceRef]


# ---------- Stage-2: extraction result for ONE document ------------------ #
class DocumentExtraction(BaseModel):
    """What the LLM returns for a single cleaned article/page."""

    model_config = ConfigDict(extra="forbid")

    doc_source: SourceRef
    trends: list[Trend] = []
    companies: list[Company] = []
    whitespace_opportunities: list[WhitespaceOpportunity] = []


# ---------- Stage-4: final aggregated answer ----------------------------- #
class ResearchReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    trends: list[Trend]
    companies: list[Company]
    whitespace_opportunities: list[WhitespaceOpportunity]
