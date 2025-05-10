# tests/core/test_settings.py
from src.core.settings import settings


def test_env_defaults():
    assert settings.model.startswith("gpt")
    assert settings.max_docs > 0