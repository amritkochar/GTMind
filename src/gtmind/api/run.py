from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from gtmind.core.search import search_sync
from gtmind.core.parse import batch_fetch_clean_sync
from gtmind.core.extract import batch_extract_sync
from gtmind.core.aggregate import aggregate
from gtmind.core.settings import settings
from gtmind.core.models import ResearchReport

app = FastAPI(title="GTMind Research API", version="0.1.0")
cli = typer.Typer(pretty_exceptions_show_locals=False)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _pipeline(query: str) -> ResearchReport:
    urls = search_sync(query)
    logging.info("🔍 Search returned %s URLs", len(urls))

    docs = batch_fetch_clean_sync(urls)
    logging.info("📄 Parsed %s docs with extractable text", len(docs))

    extracts = batch_extract_sync(docs)
    logging.info("🤖 LLM extracted insights from %s docs", len(extracts))

    report = aggregate(query, extracts)
    return report


# ---------------------- Typer CLI ---------------------------------------- #
@cli.command()
def run(
    query: str = typer.Argument(..., help="Search query, e.g. 'AI in retail'"),
    out: Path | None = typer.Option(None, help="Save JSON to this file"),
):
    """Run full pipeline from search to final JSON report."""
    report = _pipeline(query)
    data = report.model_dump()

    if out:
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        typer.echo(f"✅ Report saved to {out}")
    else:
        typer.echo(json.dumps(data, indent=2))


@cli.command()
def version():
    """Print package version."""
    import importlib.metadata as importlib_metadata

    print(importlib_metadata.version("gtmind"))


# ---------------------- FastAPI endpoint --------------------------------- #
@app.get("/report")
async def get_report(q: str):
    """GET /report?q=AI+in+retail"""
    report = await _async_pipeline(q)
    return JSONResponse(content=report.model_dump())


async def _async_pipeline(query: str) -> ResearchReport:
    """Async variant used by FastAPI (keeps same steps)."""
    from gtmind.core.search import search
    from gtmind.core.parse import batch_fetch_clean
    from gtmind.core.extract import batch_extract

    urls = await search(query)
    docs = await batch_fetch_clean(urls)
    extracts = await batch_extract(docs)
    return aggregate(query, extracts)


if __name__ == "__main__":
    cli()
