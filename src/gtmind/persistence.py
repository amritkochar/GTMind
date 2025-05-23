"""
Tiny persistence layer for ResearchReport → SQLite, based on SQLModel.
Usage:
    from gtmind.persistence import save_report

    save_report(report, db_path="research.db")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

from sqlalchemy import Integer, cast, desc
from sqlmodel import Field, Session, SQLModel, create_engine, select

from gtmind.core.models import ResearchReport


# ---------- ORM ----------------------------------------------------------- #
class ReportRow(SQLModel, table=True):
    __tablename__ = "data"
    id: Annotated[int | None, Field(primary_key=True)] = None
    query: str
    report_json: str


# ---------- public API ---------------------------------------------------- #
_engine_cache: dict[str, Any] = {}


def _engine(db_path: str) -> Any:
    if db_path not in _engine_cache:
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(engine)
        _engine_cache[db_path] = engine
    return _engine_cache[db_path]


def save_report(report: ResearchReport, db_path: str | Path = "research.db") -> int:
    """
    Persist report → SQLite and return row id.
    """
    db_path = str(db_path)
    with Session(_engine(db_path)) as sess:
        row = ReportRow(query=report.query, report_json=json.dumps(report.model_dump()))
        sess.add(row)
        sess.commit()
        sess.refresh(row)
        return row.id or -1


def list_saved_reports(db_path: str | Path) -> list[ReportRow]:
    """
    List saved reports, most recent first.
    """
    db_path = str(db_path)
    engine = _engine(db_path)
    with Session(engine) as sess:
        stmt = select(ReportRow).order_by(desc(cast(ReportRow.id, Integer)))
        return list(sess.exec(stmt))
