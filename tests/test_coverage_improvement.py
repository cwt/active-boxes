"""Additional tests to further increase code coverage."""

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import (
    Error,
)
from test_backend import InMemBackend


def test_backend_error_handling():
    """Test backend error handling when no backend is set."""
    # Save current backend
    current_backend = ap.BACKEND

    # Unset backend
    ap.use_backend(None)

    # Test get_backend raises error
    with pytest.raises(Error):
        ap.get_backend()

    # Restore backend
    ap.use_backend(current_backend)


def test_note_activity_with_all_properties():
    """Test Note activity with various properties to increase coverage."""
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

    # Create a Note with various properties
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "This is a test note",
        "attributedTo": "https://example.com/person/1",
        "published": "2023-01-01T12:00:00Z",
        "sensitive": True,
        "to": ["https://example.com/public"],
        "cc": ["https://example.com/person/2"],
        "tag": [
            {
                "type": "Mention",
                "href": "https://example.com/person/2",
                "name": "@person2@example.com",
            }
        ],
    }

    note = ap.parse_activity(note_data)
    assert isinstance(note, ap.Note)
    assert note.id == "https://example.com/note/1"
    assert note.content == "This is a test note"
    assert note.attributedTo == "https://example.com/person/1"
    assert note.published == "2023-01-01T12:00:00Z"
    assert note.sensitive == True

    # Test methods
    assert note.has_mention("https://example.com/person/2")
    assert not note.has_mention("https://example.com/person/3")

    # Test get_in_reply_to
    assert note.get_in_reply_to() is None

    # Restore backend
    ap.use_backend(None)


def test_create_activity_with_reply():
    """Test Create activity with inReplyTo property."""
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

    # Create a Note that is a reply
    reply_note_data = {
        "type": "Note",
        "id": "https://example.com/note/2",
        "content": "This is a reply",
        "attributedTo": "https://example.com/person/1",
        "inReplyTo": "https://example.com/note/1",
    }

    reply_note = ap.parse_activity(reply_note_data)
    assert isinstance(reply_note, ap.Note)
    assert reply_note.get_in_reply_to() == "https://example.com/note/1"

    # Restore backend
    ap.use_backend(None)


def test_clean_activity_function():
    """Test clean_activity function with various scenarios."""
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
    assert cleaned["type"] == "Create"
    assert cleaned["object"]["type"] == "Note"

    # Test with source field
    activity_with_source = {
        "type": "Note",
        "content": "Test note",
        "source": "Original source",
    }
    cleaned = ap.clean_activity(activity_with_source)
    assert "source" not in cleaned
    assert cleaned["type"] == "Note"
    assert cleaned["content"] == "Test note"
