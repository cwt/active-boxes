"""Tests for backend module."""

import pytest
from unittest import mock

from active_boxes.backend import AsyncBackend, Backend


class TestBackendMethods:
    """Test Backend base class methods."""

    def test_random_object_id(self):
        """Test that random_object_id returns a hex string."""
        back = _create_test_backend()
        obj_id = back.random_object_id()
        assert isinstance(obj_id, str)
        assert len(obj_id) == 16  # 8 bytes = 16 hex chars

    def test_random_object_id_unique(self):
        """Test that random_object_id returns unique values."""
        back = _create_test_backend()
        ids = {back.random_object_id() for _ in range(100)}
        assert len(ids) == 100

    def test_debug_mode_default(self):
        """Test that debug_mode returns False by default."""
        back = _create_test_backend()
        assert back.debug_mode() is False

    def test_debug_mode_true(self):
        """Test that debug_mode can be overridden to return True."""
        back = _create_test_backend_debug()
        assert back.debug_mode() is True

    def test_user_agent(self):
        """Test that user_agent returns a String."""
        back = _create_test_backend()
        ua = back.user_agent()
        assert isinstance(ua, str)
        assert "Active Boxes" in ua

    def test_extra_inboxes(self):
        """Test that extra_inboxes returns empty list by default."""
        back = _create_test_backend()
        assert back.extra_inboxes() == []

    @pytest.mark.asyncio
    async def test_check_url(self):
        """Test async check_url method."""
        back = _create_test_backend()
        await back.check_url("https://example.com")  # Should not raise


class TestAsyncBackend:
    """Test AsyncBackend class."""

    @pytest.mark.asyncio
    async def test_get_json(self):
        """Test AsyncBackend.get_json calls fetch_json."""
        back = _create_async_backend()
        back.fetch_json = mock.AsyncMock(return_value={"test": "data"})

        result = await back.get_json("https://example.com")
        assert result == {"test": "data"}
        back.fetch_json.assert_called_once_with("https://example.com")


def _create_test_backend():
    """Create a concrete Backend subclass for testing."""

    class ConcreteBackend(Backend):
        def base_url(self) -> str:
            return "https://example.com"

        def activity_url(self, obj_id: str) -> str:
            return f"https://example.com/activity/{obj_id}"

        def note_url(self, obj_id: str) -> str:
            return f"https://example.com/note/{obj_id}"

        async def fetch_iri(self, iri: str, **kwargs):
            return {"id": iri, "type": "Note"}

    return ConcreteBackend()


def _create_test_backend_debug():
    """Create a concrete Backend subclass with debug_mode=True."""

    class ConcreteBackendDebug(Backend):
        def debug_mode(self) -> bool:
            return True

        def base_url(self) -> str:
            return "https://example.com"

        def activity_url(self, obj_id: str) -> str:
            return f"https://example.com/activity/{obj_id}"

        def note_url(self, obj_id: str) -> str:
            return f"https://example.com/note/{obj_id}"

        async def fetch_iri(self, iri: str, **kwargs):
            return {"id": iri, "type": "Note"}

    return ConcreteBackendDebug()


def _create_async_backend():
    """Create an AsyncBackend instance for testing."""

    class TestAsyncBackend(AsyncBackend):
        def base_url(self) -> str:
            return "https://example.com"

        def activity_url(self, obj_id: str) -> str:
            return f"https://example.com/activity/{obj_id}"

        def note_url(self, obj_id: str) -> str:
            return f"https://example.com/note/{obj_id}"

    return TestAsyncBackend()


class TestBackendFetchJson:
    """Test Backend.fetch_json method."""

    def test_fetch_json_sync_no_loop(self):
        """Test fetch_json_sync when no event loop is running."""
        back = _create_test_backend()
        # Mock the async method that fetch_json_sync wraps
        back.fetch_json = mock.AsyncMock(return_value={"test": "data"})

        result = back.fetch_json_sync("https://example.com")
        assert result == {"test": "data"}


class TestBackendFetchIri:
    """Test Backend.fetch_iri method."""

    def test_fetch_iri_sync_no_loop(self):
        """Test fetch_iri_sync when no event loop is running."""
        back = _create_test_backend()
        # Mock the async method that fetch_iri_sync wraps
        back.fetch_iri = mock.AsyncMock(
            return_value={"id": "https://example.com"}
        )

        result = back.fetch_iri_sync("https://example.com")
        assert result == {"id": "https://example.com"}
