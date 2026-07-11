"""End-to-end checks that the pytest harness is wired correctly. See TASKS.md T04."""

import asyncio

import pytest


def test_pytest_harness_runs():
    """Trivial sync test confirming pytest discovers and executes tests from backend/."""
    assert True


@pytest.mark.asyncio
async def test_pytest_asyncio_harness_runs():
    """Async test confirming pytest-asyncio is configured (pytest.ini: asyncio_mode = auto)."""
    await asyncio.sleep(0)
    assert 1 + 1 == 2
