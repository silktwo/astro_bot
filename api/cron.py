"""Daily forecast cron Vercel function."""
from __future__ import annotations

import app as root_app


def app(environ, start_response):
    return root_app._cron(environ, start_response)
