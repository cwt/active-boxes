"""Additional tests for utility functions to increase code coverage."""

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import BadActivityError
from test_backend import InMemBackend


def test_parse_activity_exceptions():
    """Test parse_activity with various error conditions."""
    # Test with None
    with pytest.raises(BadActivityError, match="the payload has no type"):
        ap.parse_activity(None)

    # Test with string
    with pytest.raises(BadActivityError, match="the payload has no type"):
        ap.parse_activity("not a dict")

    # Test with dict missing type
    with pytest.raises(BadActivityError, match="the payload has no type"):
        ap.parse_activity({})

    # Test with unknown activity type - this will raise ValueError from enum
    with pytest.raises(ValueError):
        ap.parse_activity({"type": "UnknownType"})


def test_str_representation():
    """Test __str__ method of activities."""
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

    # Test __str__ with existing activity
    activity = ap.Create(
        id="https://example.com/create/1",
        type="Create",
        actor="https://example.com/person/1",
        object={
            "type": "Note",
            "content": "Test note",
            "id": "https://example.com/note/1",
            "attributedTo": "https://example.com/person/1",
        },
    )

    assert str(activity) == "https://example.com/create/1"

    # Test __str__ with new activity (no ID)
    new_activity = ap.Create(
        type="Create",
        actor="https://example.com/person/1",
        object={
            "type": "Note",
            "content": "Test note",
            "attributedTo": "https://example.com/person/1",
        },
    )

    # Just check that it contains the word "activity"
    assert "activity" in str(new_activity)

    # Restore backend
    ap.use_backend(None)


def test_has_type_method():
    """Test has_type method of activities."""
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

    # Test has_type method
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

    assert activity.has_type(ap.ActivityType.CREATE)
    assert activity.has_type("Create")
    assert not activity.has_type(ap.ActivityType.NOTE)

    # Restore backend
    ap.use_backend(None)
