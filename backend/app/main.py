"""Compatibility entry point for tools that still import app.main."""

from app.models.main import app

__all__ = ["app"]
