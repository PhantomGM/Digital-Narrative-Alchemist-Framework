"""
Shared pytest configuration.

Async tests run on anyio's pytest plugin, which ships with anyio (already a
dependency) rather than requiring pytest-asyncio. Mark a coroutine test with
@pytest.mark.anyio and it runs on the backend this fixture names.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.console import enable_safe_stdout  # noqa: E402

# Several suites print check marks. pytest's own capture is UTF-8, but under
# "-s" the real stdout is used, which on a piped Windows shell is cp1252 and
# would raise instead of printing.
enable_safe_stdout()


@pytest.fixture
def anyio_backend():
    """Run async tests on asyncio only; the project does not target trio."""
    return "asyncio"
