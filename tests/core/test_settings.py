# tests/core/test_models.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from gtmind.core.settings import settings


def test_env_defaults():
    assert settings.model.startswith("gpt")
    assert settings.max_docs > 0