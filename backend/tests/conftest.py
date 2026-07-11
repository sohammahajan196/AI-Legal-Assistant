"""Shared pytest fixtures/setup for the backend test suite.

Sets safe fallback values for required secrets (e.g. GOOGLE_API_KEY, see
TASKS.md T03) *before* test modules are collected, so importing `app.main` -
which eagerly instantiates `Settings()` - doesn't fail in a clean checkout
that has no real `.env`. `setdefault` is used so a real key already present
in the environment (e.g. in CI) is never overridden.
"""

import os

os.environ.setdefault("GOOGLE_API_KEY", "test-google-api-key")
