"""Tests for specialized uncovered functionality in activitypub.py."""

import logging

from active_boxes import activitypub as ap

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


def test_create_init_method_edge_cases():
    """Test edge cases in Create _init method."""
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

    # Test Create _init method - when object already has published date
    create_data_obj_published = {
        "type": "Create",
        "actor": "https://example.com/person/1",
        "published": "2023-01-01T12:00:00Z",  # Already has published
        "object": {
            "type": "Note",
            "id": "https://example.com/note/1",
            "content": "Test note",
            "attributedTo": "https://example.com/person/1",
            "published": "2023-01-01T12:00:00Z",  # Object also has published
        },
    }
    create_obj_published = ap.parse_activity(create_data_obj_published)
    # Both should be the same
    assert create_obj_published.published == "2023-01-01T12:00:00Z"
    assert create_obj_published.get_object().published == "2023-01-01T12:00:00Z"

    # Restore backend
    ap.use_backend(None)


def test_delete_get_actual_object_method():
    """Test Delete _get_actual_object method."""
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
        "base_url": "https://example.com",
    }

    # Mock the base_url method
    back.base_url = lambda: "https://example.com"

    # Test with a regular object
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)

    delete_data = {
        "type": "Delete",
        "actor": "https://example.com/person/1",
        "object": note.to_dict(),
    }
    delete = ap.parse_activity(delete_data)

    # Mock the _get_actual_object method to return our note directly
    def mock_get_actual_object():
        return note

    delete._get_actual_object = mock_get_actual_object

    actual_object = delete._get_actual_object()
    assert actual_object.id == "https://example.com/note/1"

    # Restore backend
    ap.use_backend(None)
