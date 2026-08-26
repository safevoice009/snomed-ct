"""Shared pytest fixtures: test-only API keys (never in prod code)."""
import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def _test_api_keys():
    """Provide a deterministic test API key for the whole test session."""
    os.environ.setdefault("API_KEYS", "test-dev-key")
    yield
