import subprocess
import json
from pathlib import Path
from gtmind.api.run import app
import pytest
from fastapi.testclient import TestClient
from gtmind.api.run import app

client = TestClient(app)

def test_version_cli():
    result = subprocess.run(["poetry", "run", "gtmind", "version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "0." in result.stdout  # or whatever version you expect

def test_run_cli_creates_json(tmp_path):
    out_path = tmp_path / "output.json"
    db_path = tmp_path / "output.db"

    result = subprocess.run([
        "poetry", "run", "gtmind", "run", "AI in fashion",
        "--out", str(out_path),
        "--save-sqlite", str(db_path)
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert out_path.exists()
    assert db_path.exists()

    with open(out_path) as f:
        data = json.load(f)
        assert "trends" in data


def test_get_report_success(monkeypatch):
    from gtmind.core.models import ResearchReport, Trend, Company, WhitespaceOpportunity, SourceRef

    async def _mock_async_pipeline(query: str):
        return ResearchReport(
            query=query,
            trends=[Trend(text="Trend A", sources=[SourceRef(url="https://x.com", title="X")])],
            companies=[],
            whitespace_opportunities=[],
        )

    from gtmind.api import run as mod
    monkeypatch.setattr(mod, "_async_pipeline", _mock_async_pipeline)

    response = client.get("/report?q=ai")
    assert response.status_code == 200
    assert "trends" in response.json()


def test_get_report_empty(monkeypatch):
    from gtmind.core.models import ResearchReport

    async def _mock_empty_pipeline(query: str):
        return ResearchReport(query=query, trends=[], companies=[], whitespace_opportunities=[])

    from gtmind.api import run as mod
    monkeypatch.setattr(mod, "_async_pipeline", _mock_empty_pipeline)

    response = client.get("/report?q=empty")
    assert response.status_code == 204
