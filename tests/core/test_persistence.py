# tests/core/test_persistence.py
from gtmind.core.models import ResearchReport
from gtmind.persistence import save_report


def test_save_roundtrip(tmp_path):
    db = tmp_path / "tmp.db"
    dummy = ResearchReport(query="demo", trends=[], companies=[], whitespace_opportunities=[])
    row_id = save_report(dummy, db)
    assert row_id == 1
