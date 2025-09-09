"""Additional tests to further increase code coverage."""

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import (
    Error,
    BadActivityError,
    UnexpectedActivityTypeError,
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


def test_get_url_method():
    """Test the get_url method with different URL types."""
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

    # Test with string URL
    note_data_string_url = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": "https://example.com/note/1.html",
    }
    note_string_url = ap.parse_activity(note_data_string_url)
    assert note_string_url.get_url() == "https://example.com/note/1.html"

    # Test with dict URL (Link type)
    note_data_dict_url = {
        "type": "Note",
        "id": "https://example.com/note/2",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": {
            "type": "Link",
            "href": "https://example.com/note/2.html",
        },
    }
    note_dict_url = ap.parse_activity(note_data_dict_url)
    assert note_dict_url.get_url() == "https://example.com/note/2.html"

    # Test with dict URL (invalid type)
    note_data_invalid_dict_url = {
        "type": "Note",
        "id": "https://example.com/note/3",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": {
            "type": "InvalidType",
            "href": "https://example.com/note/3.html",
        },
    }
    note_invalid_dict_url = ap.parse_activity(note_data_invalid_dict_url)
    with pytest.raises(BadActivityError):
        note_invalid_dict_url.get_url()

    # Test with list of URLs
    note_data_list_url = {
        "type": "Note",
        "id": "https://example.com/note/4",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": [
            {
                "type": "Link",
                "href": "https://example.com/note/4.txt",
                "mimeType": "text/plain",
            },
            {
                "type": "Link",
                "href": "https://example.com/note/4.html",
                "mimeType": "text/html",
            },
        ],
    }
    note_list_url = ap.parse_activity(note_data_list_url)
    assert note_list_url.get_url() == "https://example.com/note/4.html"  # Should return HTML version
    assert note_list_url.get_url("text/plain") == "https://example.com/note/4.txt"  # Should return TXT version

    # Test with list of URLs (no preferred mime type found)
    note_data_list_url_fallback = {
        "type": "Note",
        "id": "https://example.com/note/5",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": [
            {
                "type": "Link",
                "href": "https://example.com/note/5.txt",
                "mimeType": "text/plain",
            },
        ],
    }
    note_list_url_fallback = ap.parse_activity(note_data_list_url_fallback)
    assert note_list_url_fallback.get_url("text/html") == {"type": "Link", "href": "https://example.com/note/5.txt", "mimeType": "text/plain"}  # Should fallback to first object

    # Test with list of URLs (invalid type in list)
    note_data_list_invalid_url = {
        "type": "Note",
        "id": "https://example.com/note/6",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": [
            {
                "type": "InvalidType",
                "href": "https://example.com/note/6.html",
            },
        ],
    }
    note_list_invalid_url = ap.parse_activity(note_data_list_invalid_url)
    with pytest.raises(BadActivityError):
        note_list_invalid_url.get_url()

    # Test with invalid URL type
    note_data_invalid_url = {
        "type": "Note",
        "id": "https://example.com/note/7",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": 123,  # Invalid type
    }
    note_invalid_url = ap.parse_activity(note_data_invalid_url)
    with pytest.raises(BadActivityError):
        note_invalid_url.get_url()

    # Test with empty list
    note_data_empty_list_url = {
        "type": "Note",
        "id": "https://example.com/note/8",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
        "url": [],
    }
    note_empty_list_url = ap.parse_activity(note_data_empty_list_url)
    with pytest.raises(BadActivityError):
        note_empty_list_url.get_url()

    # Restore backend
    ap.use_backend(None)


def test_create_is_public_method():
    """Test the Create.is_public method."""
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

    # Test non-public activity
    private_create_data = {
        "type": "Create",
        "id": "https://example.com/create/1",
        "actor": "https://example.com/person/1",
        "to": ["https://example.com/person/2"],
        "object": {
            "type": "Note",
            "content": "Private note",
            "id": "https://example.com/note/1",
            "attributedTo": "https://example.com/person/1",
        },
    }
    private_create = ap.parse_activity(private_create_data)
    assert isinstance(private_create, ap.Create)
    assert private_create.is_public() == False

    # Test public activity (to field)
    public_create_data_to = {
        "type": "Create",
        "id": "https://example.com/create/2",
        "actor": "https://example.com/person/1",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "type": "Note",
            "content": "Public note",
            "id": "https://example.com/note/2",
            "attributedTo": "https://example.com/person/1",
        },
    }
    public_create_to = ap.parse_activity(public_create_data_to)
    assert isinstance(public_create_to, ap.Create)
    assert public_create_to.is_public() == True

    # Test public activity (cc field)
    public_create_data_cc = {
        "type": "Create",
        "id": "https://example.com/create/3",
        "actor": "https://example.com/person/1",
        "cc": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "type": "Note",
            "content": "Public note",
            "id": "https://example.com/note/3",
            "attributedTo": "https://example.com/person/1",
        },
    }
    public_create_cc = ap.parse_activity(public_create_data_cc)
    assert isinstance(public_create_cc, ap.Create)
    assert public_create_cc.is_public() == True

    # Test public activity (bto field)
    public_create_data_bto = {
        "type": "Create",
        "id": "https://example.com/create/4",
        "actor": "https://example.com/person/1",
        "bto": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "type": "Note",
            "content": "Public note",
            "id": "https://example.com/note/4",
            "attributedTo": "https://example.com/person/1",
        },
    }
    public_create_bto = ap.parse_activity(public_create_data_bto)
    assert isinstance(public_create_bto, ap.Create)
    assert public_create_bto.is_public() == True

    # Test public activity (bcc field)
    public_create_data_bcc = {
        "type": "Create",
        "id": "https://example.com/create/5",
        "actor": "https://example.com/person/1",
        "bcc": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "type": "Note",
            "content": "Public note",
            "id": "https://example.com/note/5",
            "attributedTo": "https://example.com/person/1",
        },
    }
    public_create_bcc = ap.parse_activity(public_create_data_bcc)
    assert isinstance(public_create_bcc, ap.Create)
    assert public_create_bcc.is_public() == True

    # Restore backend
    ap.use_backend(None)


def test_to_list_helper_function():
    """Test the _to_list helper function."""
    # Test with single item
    result = ap._to_list("item")
    assert result == ["item"]

    # Test with list
    result = ap._to_list(["item1", "item2"])
    assert result == ["item1", "item2"]

    # Test with None
    result = ap._to_list(None)
    assert result == [None]


def test_get_id_helper_function():
    """Test the _get_id helper function."""
    # Test with None
    result = ap._get_id(None)
    assert result is None

    # Test with string
    result = ap._get_id("https://example.com/1")
    assert result == "https://example.com/1"

    # Test with dict containing id
    result = ap._get_id({"id": "https://example.com/1"})
    assert result == "https://example.com/1"

    # Test with dict missing id
    with pytest.raises(ValueError, match="object is missing ID"):
        ap._get_id({})

    # Test with unexpected object type
    with pytest.raises(ValueError, match="unexpected object"):
        ap._get_id(123)


def test_get_actor_id_helper_function():
    """Test the _get_actor_id helper function."""
    # Test with string
    result = ap._get_actor_id("https://example.com/person/1")
    assert result == "https://example.com/person/1"

    # Test with dict containing id
    result = ap._get_actor_id({"id": "https://example.com/person/1"})
    assert result == "https://example.com/person/1"


def test_has_type_helper_function():
    """Test the _has_type helper function."""
    # Test with matching string
    result = ap._has_type("Note", ap.ActivityType.NOTE)
    assert result == True

    # Test with non-matching string
    result = ap._has_type("Note", ap.ActivityType.CREATE)
    assert result == False

    # Test with list containing match
    result = ap._has_type(["Note", "Article"], ap.ActivityType.NOTE)
    assert result == True

    # Test with list containing no match
    result = ap._has_type(["Note", "Article"], ap.ActivityType.CREATE)
    assert result == False

    # Test with empty lists
    result = ap._has_type([], [])
    assert result == False


def test_activity_type_enum():
    """Test ActivityType enum values."""
    # Test some key enum values
    assert ap.ActivityType.CREATE.value == "Create"
    assert ap.ActivityType.NOTE.value == "Note"
    assert ap.ActivityType.PERSON.value == "Person"
    assert ap.ActivityType.ORDERED_COLLECTION.value == "OrderedCollection"


def test_format_datetime_function():
    """Test format_datetime function."""
    from datetime import datetime, timezone

    # Test with timezone aware datetime
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with naive datetime (should raise ValueError)
    dt_naive = datetime(2023, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="datetime must be tz aware"):
        ap.format_datetime(dt_naive)


def test_base_activity_str_and_repr():
    """Test __str__ and __repr__ methods of BaseActivity."""
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

    # Test with activity that has ID
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)
    assert str(note) == "https://example.com/note/1"
    assert "Note" in repr(note)  # The exact format may vary

    # Test with new activity (no ID)
    new_note_data = {
        "type": "Note",
        "content": "New note",
        "attributedTo": "https://example.com/person/1",
    }
    new_note = ap.parse_activity(new_note_data)
    assert "new" in str(new_note)  # Should contain "new"
    assert "Note" in repr(new_note)  # Should contain the class name

    # Restore backend
    ap.use_backend(None)


def test_base_activity_ctx_methods():
    """Test ctx and set_ctx methods of BaseActivity."""
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

    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)

    # Test ctx method (should return None initially)
    assert note.ctx() is None

    # Test set_ctx method (using a proper object that can be weakly referenced)
    class TestContext:
        pass
    
    ctx_obj = TestContext()
    note.set_ctx(ctx_obj)
    # ctx method should return the context object
    assert note.ctx() is ctx_obj

    # Restore backend
    ap.use_backend(None)


def test_actor_id_method():
    """Test _actor_id method with various inputs."""
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

    # Create a concrete activity instance to test the method
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)

    # Test with string
    result = note._actor_id("https://example.com/person/1")
    assert result == "https://example.com/person/1"

    # Test with dict containing valid actor
    result = note._actor_id({
        "type": "Person",
        "id": "https://example.com/person/1"
    })
    assert result == "https://example.com/person/1"

    # Test with dict missing id
    with pytest.raises(BadActivityError, match="missing object id"):
        note._actor_id({
            "type": "Person"
        })

    # Test with invalid actor field
    with pytest.raises(BadActivityError, match='invalid "actor" field'):
        note._actor_id(123)

    # Restore backend
    ap.use_backend(None)
