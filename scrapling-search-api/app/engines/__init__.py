"""
Search engines package.

This package contains implementations for various search engines
and a manager to handle fallback between them.
"""

from app.engines.base import BaseEngine
from app.engines.duckduckgo import DuckDuckGoEngine
from app.engines.bing_scrapling import BingEngine
# from app.engines.google import GoogleEngine  # Disabled: Playwright sync API doesn't work in async context
from app.engines.manager import EngineManager

__all__ = [
    "BaseEngine",
    "DuckDuckGoEngine",
    "BingEngine",
    # "GoogleEngine",  # Disabled
    "EngineManager",
]
