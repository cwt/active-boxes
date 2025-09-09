"""Test for to_dict method to increase code coverage."""

from active_boxes import activitypub as ap
from test_backend import InMemBackend


def test_to_dict_method():
    """Test to_dict method with various options."""
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

    # Create an activity
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

    # Test basic to_dict
    data = activity.to_dict()
    assert "type" in data
    assert "actor" in data
    assert "object" in data

    # Test with embed=True
    data = activity.to_dict(embed=True)
    assert "@context" not in data
    assert "signature" not in data

    # Test with embed_object_id_only=True
    data = activity.to_dict(embed_object_id_only=True)
    assert isinstance(data["object"], str)
    assert data["object"] == "https://example.com/note/1"

    # Restore backend
    ap.use_backend(None)
