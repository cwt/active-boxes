"""Additional tests to increase code coverage for activitypub module."""

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import (
    BadActivityError,
    UnexpectedActivityTypeError,
    Error,
)


def test_base_activity_exceptions(backend):
    """Test exception paths in BaseActivity initialization."""
    # Add actor to mock data
    backend.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test Create activity with missing actor when required
    with pytest.raises(BadActivityError, match="missing actor"):
        ap.Create(
            type="Create",
            object={
                "type": "Note",
                "content": "Test note",
                "id": "https://example.com/note/1",
            },
        )

    # Test with invalid object type
    with pytest.raises(BadActivityError):
        ap.Create(
            type="Create",
            actor="https://example.com/person/1",
            object=123,  # Invalid object type
        )

    # Test with object missing type
    with pytest.raises(BadActivityError, match="invalid object, missing type"):
        ap.Create(
            type="Create",
            actor="https://example.com/person/1",
            object={},  # Empty dict
        )


def test_get_object_id_exceptions(backend):
    """Test exception paths in get_object_id method."""
    # Add actor to mock data
    backend.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Create an activity with an invalid object reference
    activity = ap.Create(
        type="Create",
        actor="https://example.com/person/1",
        object={
            "type": "Note",
            "content": "Test note",
            "id": "https://example.com/note/1",
            "attributedTo": "https://example.com/person/1",
        },
    )

    # Test with invalid object type
    activity._data["object"] = 123  # Invalid type

    # Reset the cached object to make sure we're testing the direct access
    activity._BaseActivity__obj = None

    with pytest.raises(ValueError, match="invalid object"):
        activity.get_object_id()


def test_get_actor_exceptions(backend):
    """Test exception paths in get_actor method."""
    # Add actors to mock data
    backend.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test get_actor with invalid actor type
    backend.FETCH_MOCK["https://example.com/invalid/actor"] = {
        "type": "InvalidActorType",
        "id": "https://example.com/invalid/actor",
    }

    # Test that activity creation raises UnexpectedActivityTypeError for invalid actor type
    with pytest.raises(UnexpectedActivityTypeError):
        activity = ap.Create(
            type="Create",
            actor="https://example.com/invalid/actor",
            object={
                "type": "Note",
                "content": "Test note",
                "id": "https://example.com/note/1",
                "attributedTo": "https://example.com/person/1",
            },
        )


def test_get_backend_without_initialization():
    """Test that get_backend raises error when no backend is initialized."""
    # Test get_backend raises error
    with pytest.raises(Error):
        ap.get_backend()


def test_format_datetime_exceptions():
    """Test format_datetime with naive datetime."""
    from datetime import datetime

    # Test with naive datetime (should raise ValueError)
    dt = datetime(2023, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="datetime must be tz aware"):
        ap.format_datetime(dt)


def test_has_type_edge_cases():
    """Test _has_type function with edge cases."""
    # Test with empty lists
    assert not ap._has_type([], [])

    # Test with mixed types
    assert ap._has_type("Note", ap.ActivityType.NOTE)
    assert not ap._has_type("Note", ap.ActivityType.CREATE)


def test_to_list_edge_cases():
    """Test _to_list function with edge cases."""
    # Test with None
    assert ap._to_list(None) == [None]

    # Test with list
    assert ap._to_list([1, 2, 3]) == [1, 2, 3]

    # Test with single item
    assert ap._to_list("item") == ["item"]


def test_get_id_edge_cases():
    """Test _get_id function with edge cases."""
    # Test with None
    assert ap._get_id(None) is None

    # Test with string
    assert ap._get_id("https://example.com/1") == "https://example.com/1"

    # Test with dict containing id
    assert (
        ap._get_id({"id": "https://example.com/1"}) == "https://example.com/1"
    )

    # Test with dict missing id
    with pytest.raises(ValueError, match="object is missing ID"):
        ap._get_id({})

    # Test with unexpected object type
    with pytest.raises(ValueError, match="unexpected object"):
        ap._get_id(123)


def test_get_actor_id_edge_cases():
    """Test _get_actor_id function with edge cases."""
    # Test with string
    assert (
        ap._get_actor_id("https://example.com/person/1")
        == "https://example.com/person/1"
    )

    # Test with dict containing id
    assert (
        ap._get_actor_id({"id": "https://example.com/person/1"})
        == "https://example.com/person/1"
    )


def test_activity_type_enum():
    """Test ActivityType enum values."""
    # Test some key enum values
    assert ap.ActivityType.CREATE.value == "Create"
    assert ap.ActivityType.NOTE.value == "Note"
    assert ap.ActivityType.PERSON.value == "Person"
    assert ap.ActivityType.ORDERED_COLLECTION.value == "OrderedCollection"


def test_clean_activity():
    """Test clean_activity function."""
    # Test with activity containing bto field
    activity = {
        "type": "Note",
        "content": "Test note",
        "bto": ["https://example.com/person/1"],
    }
    cleaned = ap.clean_activity(activity)
    assert "bto" not in cleaned
    assert cleaned["type"] == "Note"
    assert cleaned["content"] == "Test note"

    # Test with Create activity containing bcc field
    create_activity = {
        "type": "Create",
        "object": {
            "type": "Note",
            "content": "Test note",
            "bcc": ["https://example.com/person/1"],
        },
    }
    cleaned = ap.clean_activity(create_activity)
    assert "bcc" not in cleaned["object"]
