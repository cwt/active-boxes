"""Final tests to reach 85% code coverage."""

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import BadActivityError
from test_backend import InMemBackend


def test_actor_validation_edge_cases():
    """Test edge cases in actor validation."""
    back = InMemBackend()
    ap.use_backend(back)

    # Add valid actor to mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test with invalid actor dict (missing id)
    with pytest.raises(BadActivityError, match="missing object id"):
        ap.Create(
            type="Create",
            actor={"type": "Person"},  # Missing id
            object={
                "type": "Note",
                "content": "Test note",
                "id": "https://example.com/note/1",
                "attributedTo": "https://example.com/person/1",
            },
        )

    # Test with invalid actor type
    with pytest.raises(BadActivityError, match='invalid "actor" field'):
        ap.Create(
            type="Create",
            actor=123,  # Invalid type
            object={
                "type": "Note",
                "content": "Test note",
                "id": "https://example.com/note/1",
                "attributedTo": "https://example.com/person/1",
            },
        )

    # Restore backend
    ap.use_backend(None)


def test_object_validation_edge_cases():
    """Test edge cases in object validation."""
    back = InMemBackend()
    ap.use_backend(back)

    # Add actor to mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test Create with object missing attributedTo
    with pytest.raises(BadActivityError, match="Note is missing attributedTo"):
        ap.Create(
            type="Create",
            actor="https://example.com/person/1",
            object={
                "type": "Note",
                "content": "Test note",
                "id": "https://example.com/note/1",
                # Missing attributedTo
            },
        )

    # Restore backend
    ap.use_backend(None)


def test_collection_activities_with_items():
    """Test Collection and OrderedCollection with various item types."""
    back = InMemBackend()
    ap.use_backend(back)

    # Test Collection with string items
    collection_data = {
        "type": "Collection",
        "id": "https://example.com/collection/1",
        "items": ["https://example.com/item/1", "https://example.com/item/2"],
        "totalItems": 2,
    }

    collection = ap.parse_activity(collection_data)
    assert isinstance(collection, ap.Collection)
    assert collection.id == "https://example.com/collection/1"
    assert collection.totalItems == 2

    # Test OrderedCollection with string items
    ordered_collection_data = {
        "type": "OrderedCollection",
        "id": "https://example.com/ordered-collection/1",
        "orderedItems": [
            "https://example.com/item/1",
            "https://example.com/item/2",
        ],
        "totalItems": 2,
    }

    ordered_collection = ap.parse_activity(ordered_collection_data)
    assert isinstance(ordered_collection, ap.OrderedCollection)
    assert ordered_collection.id == "https://example.com/ordered-collection/1"
    assert ordered_collection.totalItems == 2

    # Restore backend
    ap.use_backend(None)


def test_context_handling():
    """Test context handling in activities."""
    back = InMemBackend()
    ap.use_backend(back)

    # Add actor to mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test activity with custom context
    activity_data = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"custom": "http://example.com#custom"},
        ],
        "type": "Create",
        "actor": "https://example.com/person/1",
        "object": {
            "type": "Note",
            "content": "Test note",
            "id": "https://example.com/note/1",
            "attributedTo": "https://example.com/person/1",
        },
    }

    activity = ap.parse_activity(activity_data)
    assert isinstance(activity, ap.Create)
    # Check that context was properly handled
    assert "https://www.w3.org/ns/activitystreams" in activity._data["@context"]
    assert isinstance(activity._data["@context"][-1], dict)
    # The context gets modified by the activity initialization, so just check it's a dict

    # Restore backend
    ap.use_backend(None)


def test_format_datetime_edge_cases():
    """Test format_datetime with various edge cases."""
    from datetime import datetime, timezone, timedelta

    # Test with timezone aware datetime with microseconds
    dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with timezone aware datetime in different timezone
    dt = datetime(2023, 1, 1, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with naive datetime (should raise ValueError)
    dt = datetime(2023, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="datetime must be tz aware"):
        ap.format_datetime(dt)
