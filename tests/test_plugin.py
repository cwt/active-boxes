"""Tests for the ActivityPub plugin protocol."""

import pytest

from active_boxes.plugin import (
    ActivityPubPlugin,
    CollectionPlugin,
    DeliveryPlugin,
    InboxPlugin,
    StoragePlugin,
)
from active_boxes import activitypub as ap

from test_backend import InMemBackend


class MinimalPlugin:
    """Minimal implementation of ActivityPubPlugin for testing."""

    BASE_URL = "https://example.com"

    def base_url(self) -> str:
        return self.BASE_URL

    def activity_url(self, obj_id: str) -> str:
        return f"{self.BASE_URL}/activity/{obj_id}"

    def note_url(self, obj_id: str) -> str:
        return f"{self.BASE_URL}/note/{obj_id}"

    async def deliver_activity(
        self,
        activity: dict,
        inbox: str,
        actor: dict,
    ) -> bool:
        return True

    async def receive_activity(
        self,
        activity: dict,
        source_inbox: str | None = None,
    ) -> bool:
        return True

    def is_duplicate(self, activity_id: str) -> bool:
        return False

    def extra_inboxes(self) -> list[str]:
        return []

    def store_activity(
        self,
        activity: dict,
        recipient_inbox: str | None = None,
    ) -> None:
        pass

    def get_activity(self, activity_id: str) -> dict | None:
        return None

    def store_actor(self, actor: dict) -> None:
        pass

    def get_actor(self, actor_id: str) -> dict | None:
        return None


class FullFeaturedPlugin(MinimalPlugin):
    """Plugin with all optional methods implemented."""

    def get_outbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> dict:
        return {
            "type": "OrderedCollection",
            "id": f"{self.BASE_URL}/outbox",
            "totalItems": 0,
            "first": f"{self.BASE_URL}/outbox?page=1",
        }

    def get_inbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> dict:
        return {
            "type": "OrderedCollection",
            "id": f"{self.BASE_URL}/inbox",
            "totalItems": 0,
            "first": f"{self.BASE_URL}/inbox?page=1",
        }

    def get_followers(self, actor_id: str) -> dict:
        return {
            "type": "Collection",
            "id": f"{actor_id}/followers",
            "totalItems": 0,
        }

    def get_following(self, actor_id: str) -> dict:
        return {
            "type": "Collection",
            "id": f"{actor_id}/following",
            "totalItems": 0,
        }

    def get_liked(self, actor_id: str) -> dict:
        return {
            "type": "Collection",
            "id": f"{actor_id}/liked",
            "totalItems": 0,
        }

    def verify_origin(self, activity: dict, actor: dict) -> bool:
        return True


class TestPluginProtocol:
    """Test that plugin classes satisfy the Protocol."""

    def test_full_plugin_satisfies_protocol(self):
        """Full featured plugin should satisfy ActivityPubPlugin protocol."""
        plugin = FullFeaturedPlugin()
        assert isinstance(plugin, ActivityPubPlugin)

    def test_delivery_plugin_protocol(self):
        """Plugin should satisfy DeliveryPlugin protocol."""
        plugin = MinimalPlugin()
        assert isinstance(plugin, DeliveryPlugin)

    def test_inbox_plugin_protocol(self):
        """Plugin should satisfy InboxPlugin protocol."""
        plugin = MinimalPlugin()
        assert isinstance(plugin, InboxPlugin)

    def test_storage_plugin_protocol(self):
        """Plugin should satisfy StoragePlugin protocol."""
        plugin = MinimalPlugin()
        assert isinstance(plugin, StoragePlugin)

    def test_collection_plugin_protocol(self):
        """Plugin with collection methods should satisfy CollectionPlugin."""
        plugin = FullFeaturedPlugin()
        assert isinstance(plugin, CollectionPlugin)


class TestPluginMethods:
    """Test plugin method signatures and behavior."""

    def test_base_url_returns_string(self):
        """base_url() should return a string."""
        plugin = MinimalPlugin()
        assert isinstance(plugin.base_url(), str)
        assert plugin.base_url() == "https://example.com"

    def test_activity_url_returns_string(self):
        """activity_url() should return a string with obj_id."""
        plugin = MinimalPlugin()
        result = plugin.activity_url("abc123")
        assert isinstance(result, str)
        assert "abc123" in result

    def test_note_url_returns_string(self):
        """note_url() should return a string with obj_id."""
        plugin = MinimalPlugin()
        result = plugin.note_url("xyz789")
        assert isinstance(result, str)
        assert "xyz789" in result

    def test_is_duplicate_returns_bool(self):
        """is_duplicate() should return a bool."""
        plugin = MinimalPlugin()
        assert isinstance(plugin.is_duplicate("any-id"), bool)

    def test_extra_inboxes_returns_list(self):
        """extra_inboxes() should return a list."""
        plugin = MinimalPlugin()
        result = plugin.extra_inboxes()
        assert isinstance(result, list)


class TestCollectionMethods:
    """Test collection plugin methods."""

    def test_get_outbox_returns_dict(self):
        """get_outbox() should return a dict."""
        plugin = FullFeaturedPlugin()
        result = plugin.get_outbox("https://example.com/user/alice")
        assert isinstance(result, dict)
        assert result["type"] == "OrderedCollection"

    def test_get_inbox_returns_dict(self):
        """get_inbox() should return a dict."""
        plugin = FullFeaturedPlugin()
        result = plugin.get_inbox("https://example.com/user/alice")
        assert isinstance(result, dict)
        assert result["type"] == "OrderedCollection"

    def test_get_followers_returns_dict(self):
        """get_followers() should return a dict."""
        plugin = FullFeaturedPlugin()
        result = plugin.get_followers("https://example.com/user/alice")
        assert isinstance(result, dict)
        assert result["type"] == "Collection"

    def test_get_following_returns_dict(self):
        """get_following() should return a dict."""
        plugin = FullFeaturedPlugin()
        result = plugin.get_following("https://example.com/user/alice")
        assert isinstance(result, dict)
        assert result["type"] == "Collection"

    def test_get_liked_returns_dict(self):
        """get_liked() should return a dict."""
        plugin = FullFeaturedPlugin()
        result = plugin.get_liked("https://example.com/user/alice")
        assert isinstance(result, dict)
        assert result["type"] == "Collection"

    def test_verify_origin_returns_bool(self):
        """verify_origin() should return a bool."""
        plugin = FullFeaturedPlugin()
        result = plugin.verify_origin({}, {})
        assert isinstance(result, bool)


class TestInMemoryDeduplication:
    """Test in-memory deduplication implementation."""

    def test_is_duplicate_with_set(self) -> None:
        """Test deduplication using a simple set."""
        seen: set[str] = set()

        def is_duplicate(activity_id: str) -> bool:
            if activity_id in seen:
                return True
            seen.add(activity_id)
            return False

        assert is_duplicate("activity-1") is False
        assert is_duplicate("activity-1") is True
        assert is_duplicate("activity-2") is False
        assert is_duplicate("activity-1") is True


class TestAsyncMethods:
    """Test that async methods work correctly."""

    @pytest.mark.asyncio
    async def test_deliver_activity_async(self):
        """deliver_activity should be awaitable."""
        plugin = MinimalPlugin()

        async def mock_deliver():
            return await plugin.deliver_activity(
                {"type": "Create"},
                "https://example.com/inbox",
                {"id": "https://example.com/actor"},
            )

        result = await mock_deliver()
        assert result is True

    @pytest.mark.asyncio
    async def test_receive_activity_async(self):
        """receive_activity should be awaitable."""
        plugin = MinimalPlugin()

        async def mock_receive():
            return await plugin.receive_activity(
                {"type": "Create", "id": "https://example.com/activity/1"}
            )

        result = await mock_receive()
        assert result is True


class TestPluginWithBackend:
    """Test plugin integration with activitypub backend."""

    def test_plugin_can_be_used_with_backend(self):
        """Plugin should work with activitypub module."""
        back = InMemBackend()
        ap.use_backend(back)

        plugin = FullFeaturedPlugin()
        assert plugin.base_url() == "https://example.com"

        outbox = plugin.get_outbox("https://example.com/user/alice")
        assert outbox["type"] == "OrderedCollection"

        ap.use_backend(None)
