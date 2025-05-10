# src/gtmind/__init__.py
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gtmind")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
