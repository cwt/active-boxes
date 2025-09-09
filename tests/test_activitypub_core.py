"""Core ActivityPub functionality tests."""

import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import (
    BadActivityError,
    UnexpectedActivityTypeError,
    Error,
    ActivityGoneError,
    ActivityNotFoundError,
)

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


def test_format_datetime():
    # Test with timezone aware datetime
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with timezone aware datetime with microseconds
    dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with timezone aware datetime in different timezone
    dt = datetime(2023, 1, 1, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with naive datetime (should raise ValueError)
    dt = datetime(2023, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError):
        ap.format_datetime(dt)


def test_backend_functions():
    # Test get_backend without initialization
    with pytest.raises(ap.Error):
        ap.get_backend()

    # Test use_backend and get_backend
    back = InMemBackend()
    ap.use_backend(back)
    assert ap.get_backend() == back

    # Test use_backend with None
    ap.use_backend(None)
    with pytest.raises(ap.Error):
        ap.get_backend()

    # Restore backend
    ap.use_backend(back)


def test_activity_type_enum():
    # Test that ActivityType enum values are correct
    assert ap.ActivityType.CREATE.value == "Create"
    assert ap.ActivityType.ANNOUNCE.value == "Announce"
    assert ap.ActivityType.LIKE.value == "Like"
    assert ap.ActivityType.NOTE.value == "Note"
    assert ap.ActivityType.PERSON.value == "Person"


def test_parse_activity_errors():
    back = InMemBackend()
    ap.use_backend(back)

    # Test with None
    with pytest.raises(BadActivityError):
        ap.parse_activity(None)

    # Test with string
    with pytest.raises(BadActivityError):
        ap.parse_activity("not a dict")

    # Test with dict missing type
    with pytest.raises(BadActivityError):
        ap.parse_activity({})

    # Test with unknown activity type
    with pytest.raises(ValueError):
        ap.parse_activity({"type": "UnknownType"})

    # Restore backend
    ap.use_backend(None)


def test_activity_type_checking():
    # Test _has_type function
    assert ap._has_type("Note", ap.ActivityType.NOTE)
    assert ap._has_type("Note", "Note")
    assert ap._has_type(["Note", "Article"], ap.ActivityType.NOTE)
    assert not ap._has_type("Note", ap.ActivityType.CREATE)

    # Test with multiple types
    assert ap._has_type("Note", [ap.ActivityType.NOTE, ap.ActivityType.ARTICLE])
    assert ap._has_type(
        "Article", [ap.ActivityType.NOTE, ap.ActivityType.ARTICLE]
    )
    assert not ap._has_type(
        "Person", [ap.ActivityType.NOTE, ap.ActivityType.ARTICLE]
    )


def test_get_id_function():
    # Test _get_id function
    assert ap._get_id(None) is None
    assert ap._get_id("https://example.com/1") == "https://example.com/1"
    assert (
        ap._get_id({"id": "https://example.com/1"}) == "https://example.com/1"
    )

    with pytest.raises(ValueError, match="object is missing ID"):
        ap._get_id({})

    with pytest.raises(ValueError, match="unexpected object"):
        ap._get_id(123)


def test_get_actor_id_function():
    # Test _get_actor_id function
    assert (
        ap._get_actor_id("https://example.com/person/1")
        == "https://example.com/person/1"
    )
    assert (
        ap._get_actor_id({"id": "https://example.com/person/1"})
        == "https://example.com/person/1"
    )


def test_to_list_function():
    # Test _to_list function
    assert ap._to_list("item") == ["item"]
    assert ap._to_list(["item1", "item2"]) == ["item1", "item2"]
    assert ap._to_list(None) == [None]


def test_clean_activity():
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


def test_activity_type_enum_additional():
    """Test ActivityType enum values."""
    # Test some key enum values
    assert ap.ActivityType.CREATE.value == "Create"
    assert ap.ActivityType.NOTE.value == "Note"
    assert ap.ActivityType.PERSON.value == "Person"
    assert ap.ActivityType.ORDERED_COLLECTION.value == "OrderedCollection"


def test_clean_activity_additional():
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


def test_validate_actor_method():
    """Test _validate_actor method with various scenarios."""
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

    # Test with valid actor string
    result = note._validate_actor("https://example.com/person/1")
    assert result == "https://example.com/person/1"

    # Test with valid actor dict
    result = note._validate_actor(
        {"type": "Person", "id": "https://example.com/person/1"}
    )
    assert result == "https://example.com/person/1"

    # Test with actor that returns None from backend
    back.FETCH_MOCK["https://example.com/none/1"] = None
    with pytest.raises(BadActivityError):
        note._validate_actor("https://example.com/none/1")

    # Test with actor missing id from backend
    back.FETCH_MOCK["https://example.com/no-id/1"] = {"type": "Person"}
    with pytest.raises(BadActivityError):
        note._validate_actor("https://example.com/no-id/1")

    # Test with invalid actor field (not string or dict)
    with pytest.raises(BadActivityError, match='invalid "actor" field'):
        note._validate_actor(123)

    # Restore backend
    ap.use_backend(None)


def test_validate_actor_exceptions():
    """Test _validate_actor method exception paths."""
    back = InMemBackend()
    ap.use_backend(back)

    # Create a concrete activity instance to test the method
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)

    # Test with backend that raises ActivityGoneError (should propagate)
    class MockGoneBackend:
        def fetch_iri(self, iri):
            raise ActivityGoneError("Gone")

    ap.use_backend(MockGoneBackend())
    with pytest.raises(ActivityGoneError):
        note._validate_actor("https://example.com/person/1")

    # Test with backend that raises ActivityNotFoundError (should propagate)
    class MockNotFoundBackend:
        def fetch_iri(self, iri):
            raise ActivityNotFoundError("Not Found")

    ap.use_backend(MockNotFoundBackend())
    with pytest.raises(ActivityNotFoundError):
        note._validate_actor("https://example.com/person/1")

    # Test with backend that raises other exception (should become BadActivityError)
    class MockOtherErrorBackend:
        def fetch_iri(self, iri):
            raise Exception("Other error")

    ap.use_backend(MockOtherErrorBackend())
    with pytest.raises(BadActivityError, match="failed to validate actor"):
        note._validate_actor("https://example.com/person/1")

    # Restore backend
    ap.use_backend(back)
    ap.use_backend(None)


def test_get_object_id_method():
    """Test get_object_id method."""
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

    # Create activity with dict object
    create_data_dict = {
        "type": "Create",
        "id": "https://example.com/create/2",
        "actor": "https://example.com/person/1",
        "object": {
            "type": "Note",
            "id": "https://example.com/note/2",
            "content": "Test note",
            "attributedTo": "https://example.com/person/1",
        },
    }
    create_dict = ap.parse_activity(create_data_dict)
    assert create_dict.get_object_id() == "https://example.com/note/2"

    # Test with invalid object type
    # Directly modify the object to an invalid type
    create_dict._data["object"] = 123
    # Reset cached object
    create_dict._BaseActivity__obj = None
    with pytest.raises(ValueError, match="invalid object"):
        create_dict.get_object_id()

    # Restore backend
    ap.use_backend(None)


def test_reset_object_cache():
    """Test reset_object_cache method."""
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

    # Create a Note (not a Create) to avoid issues with _init
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "Test note",
        "attributedTo": "https://example.com/person/1",
    }
    note = ap.parse_activity(note_data)

    # Manually set up an object to test caching
    note._data["object"] = {
        "type": "Note",
        "id": "https://example.com/note/2",
        "content": "Test note 2",
        "attributedTo": "https://example.com/person/1",
    }

    # Get object (this should cache it)
    obj1 = note.get_object()

    # Reset cache
    note.reset_object_cache()

    # Modify the object data
    note._data["object"]["content"] = "Modified note"

    # Get object again (this should process the modified data)
    obj2 = note.get_object()

    # They should be different objects with different content
    assert obj1 is not obj2
    assert obj2.content == "Modified note"

    # Restore backend
    ap.use_backend(None)


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


# Additional tests from coverage files


def test_format_datetime_edge_cases_additional():
    """Test edge cases for format_datetime function."""
    from datetime import datetime, timezone

    # Test with timezone aware datetime with microseconds
    dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"

    # Test with timezone aware datetime in different timezone
    from datetime import timedelta

    dt = datetime(2023, 1, 1, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    assert ap.format_datetime(dt) == "2023-01-01T12:00:00Z"


def test_backend_functions_edge_cases():
    """Test edge cases for backend functions."""
    # Test get_backend without initialization
    ap.use_backend(None)
    with pytest.raises(ap.Error):
        ap.get_backend()

    # Test use_backend with None
    ap.use_backend(None)
    with pytest.raises(ap.Error):
        ap.get_backend()


def test_get_backend_uninitialized():
    """Test get_backend function when backend is not initialized."""
    # Save current backend
    original_backend = ap.BACKEND

    # Unset backend
    ap.use_backend(None)

    # Test that get_backend raises error
    with pytest.raises(ap.Error):
        ap.get_backend()

    # Restore backend
    ap.use_backend(original_backend)


def test_activity_type_validation():
    """Test activity type validation in parse_activity."""
    back = InMemBackend()
    ap.use_backend(back)

    # Test with unexpected activity type (should raise ValueError from enum first)
    with pytest.raises(ValueError):
        ap.parse_activity(
            {"type": "UnknownType"}, expected=ap.ActivityType.NOTE
        )

    # Restore backend
    ap.use_backend(None)


def test_base_activity_init_edge_cases():
    """Test edge cases in BaseActivity __init__ method."""
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

    # Test with None values in kwargs (should be filtered out)
    activity_data = {
        "type": "Create",
        "actor": "https://example.com/person/1",
        "object": {
            "type": "Note",
            "content": "Test note",
            "id": "https://example.com/note/1",
            "attributedTo": "https://example.com/person/1",
        },
        "summary": None,  # Should be filtered out
    }
    activity = ap.parse_activity(activity_data)
    # Verify the None value was filtered out
    assert "summary" not in activity._data

    # Restore backend
    ap.use_backend(None)


def test_context_handling_core():
    """Test context handling in BaseActivity __init__ method."""
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

    # Test with existing context that ends with dict
    activity_data = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"custom": "http://example.com/ns#"},
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
    # Verify context was processed
    assert "@context" in activity._data
    assert isinstance(activity._data["@context"], list)

    # Restore backend
    ap.use_backend(None)


def test_clean_activity_edge_cases():
    """Test edge cases in clean_activity function."""
    # Test with activity containing featured field
    activity = {
        "type": "Note",
        "content": "Test note",
        "featured": "https://example.com/featured",
    }
    cleaned = ap.clean_activity(activity)
    assert (
        "featured" in cleaned
    )  # featured should not be removed by clean_activity

    # Test with Create activity containing various fields to be cleaned
    create_activity = {
        "type": "Create",
        "object": {
            "type": "Note",
            "content": "Test note",
            "bto": ["https://example.com/person/1"],
            "bcc": ["https://example.com/person/2"],
        },
        "bto": ["https://example.com/person/3"],
        "bcc": ["https://example.com/person/4"],
    }
    cleaned = ap.clean_activity(create_activity)
    assert "bto" not in cleaned
    assert "bcc" not in cleaned
    assert "bto" not in cleaned["object"]
    assert "bcc" not in cleaned["object"]
