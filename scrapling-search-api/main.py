"""
Entry point for Scrapling Search API.

This is a simple wrapper that imports the app from the modular structure.
Allows running with: uvicorn main:app
"""

from app.main import app

__all__ = ["app"]

