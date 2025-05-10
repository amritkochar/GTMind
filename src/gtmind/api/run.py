# src/gtmind/api/run.py
from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gtmind.core.aggregate import aggregate
from gtmind.core.extract import batch_extract_sync
from gtmind.core.models import ResearchReport
from gtmind.core.parse import batch_fetch_clean_sync
from gtmind.core.search import search_sync
from gtmind.persistence import save_report

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="GTMind Research API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Typer CLI setup
# -----------------------------------------------------------------------------
cli = typer.Typer(pretty_exceptions_show_locals=False)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# -----------------------------------------------------------------------------
# Pipeline helpers
# -----------------------------------------------------------------------------
def _pipeline(query: str) -> ResearchReport:
    urls = search_sync(query)
    logging.info("🔍  Search returned %s URLs", len(urls))

    docs = batch_fetch_clean_sync(urls)
    if not docs:
        raise RuntimeError(f"No clean content found for '{query}' — check your query or sources.")

    logging.info("📄  Parsed %s docs with extractable text", len(docs))

    extracts = batch_extract_sync(docs)
    logging.info("🤖  LLM extracted insights from %s docs", len(extracts))

    return aggregate(query, extracts)


async def _async_pipeline(query: str) -> ResearchReport:
    """Async variant for FastAPI (non-blocking)."""
    from gtmind.core.extract import batch_extract
    from gtmind.core.parse import batch_fetch_clean
    from gtmind.core.search import search

    urls = await search(query)
    docs = await batch_fetch_clean(urls)
    extracts = await batch_extract(docs)
    return aggregate(query, extracts)


# -----------------------------------------------------------------------------
# Typer commands
# -----------------------------------------------------------------------------
@cli.command()
def run(
    query: str = typer.Argument(..., help="Search query (e.g. 'AI in retail')"),
    out: Path | None = typer.Option(None, help="Write pretty JSON to this path"),
    save_sqlite: Path | None = typer.Option(
        None, help="Persist report into this SQLite DB (creates if absent)"
    ),
):
    """Execute full pipeline and optionally save results."""
    report = _pipeline(query)
    data = report.model_dump()

    # save pretty JSON file
    if out:
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        typer.echo(f"✅ JSON saved to {out}")

    # persist to SQLite
    if save_sqlite:
        row_id = save_report(report, save_sqlite)
        typer.echo(f"💾 Stored in {save_sqlite} (row id {row_id})")

    # default: print to stdout if no --out flag
    if not out:
        typer.echo(json.dumps(data, indent=2))


@cli.command()
def version():
    """Print installed package version."""
    import importlib.metadata as importlib_metadata

    typer.echo(importlib_metadata.version("gtmind"))


# -----------------------------------------------------------------------------
# FastAPI route
# -----------------------------------------------------------------------------
@app.get("/report")
async def get_report(q: str):
    report = await _async_pipeline(q)

    if not (report.trends or report.companies or report.whitespace_opportunities):
        return JSONResponse(
            status_code=204,
            content={"detail": "No insights found for this query."}
        )

    return JSONResponse(content=report.model_dump())



# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    cli()
