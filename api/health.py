"""Health-check Vercel function."""
from __future__ import annotations

from app import _resp


def app(environ, start_response):
    return _resp(start_response, "200 OK", b"astro_bot ok")
