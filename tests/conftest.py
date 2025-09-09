"""Shared test configuration and fixtures."""

import pytest
from test_backend import InMemBackend
import active_boxes.activitypub as ap


@pytest.fixture
def backend():
    """Provide a backend instance for tests and ensure cleanup."""
    back = InMemBackend()
    ap.use_backend(back)
    yield back
    ap.use_backend(None)
