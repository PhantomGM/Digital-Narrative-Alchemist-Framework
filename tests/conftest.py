"""
Shared pytest configuration.

Async tests run on anyio's pytest plugin, which ships with anyio (already a
dependency) rather than requiring pytest-asyncio. Mark a coroutine test with
@pytest.mark.anyio and it runs on the backend this fixture names.
"""

import pytest


@pytest.fixture
def anyio_backend():
    """Run async tests on asyncio only; the project does not target trio."""
    return "asyncio"
