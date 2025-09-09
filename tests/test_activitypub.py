import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from active_boxes import activitypub as ap
from active_boxes.errors import (
    BadActivityError,
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


def test_person_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Test creating a Person activity
    person_data = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    person = ap.parse_activity(person_data)
    assert isinstance(person, ap.Person)
    assert person.id == "https://example.com/person/1"
    assert person.name == "Test User"
    assert person.preferredUsername == "testuser"

    # Restore backend
    ap.use_backend(None)


def test_note_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Test creating a Note activity
    note_data = {
        "type": "Note",
        "id": "https://example.com/note/1",
        "content": "This is a test note",
        "attributedTo": "https://example.com/person/1",
    }

    note = ap.parse_activity(note_data)
    assert isinstance(note, ap.Note)
    assert note.id == "https://example.com/note/1"
    assert note.content == "This is a test note"
    assert note.attributedTo == "https://example.com/person/1"

    # Restore backend
    ap.use_backend(None)


def test_create_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Add the actor to the mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test creating a Create activity
    create_data = {
        "type": "Create",
        "id": "https://example.com/create/1",
        "actor": "https://example.com/person/1",
        "object": {
            "type": "Note",
            "id": "https://example.com/note/1",
            "content": "This is a test note",
            "attributedTo": "https://example.com/person/1",
        },
    }

    create = ap.parse_activity(create_data)
    assert isinstance(create, ap.Create)
    assert create.id == "https://example.com/create/1"
    assert create.actor == "https://example.com/person/1"

    obj = create.get_object()
    assert isinstance(obj, ap.Note)
    assert obj.id == "https://example.com/note/1"

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


def test_collection_activities():
    back = InMemBackend()
    ap.use_backend(back)

    # Test Collection activity
    collection_data = {
        "type": "Collection",
        "id": "https://example.com/collection/1",
        "items": ["https://example.com/item/1", "https://example.com/item/2"],
    }

    collection = ap.parse_activity(collection_data)
    assert isinstance(collection, ap.Collection)
    assert collection.id == "https://example.com/collection/1"

    # Test OrderedCollection activity
    ordered_collection_data = {
        "type": "OrderedCollection",
        "id": "https://example.com/ordered-collection/1",
        "orderedItems": [
            "https://example.com/item/1",
            "https://example.com/item/2",
        ],
    }

    ordered_collection = ap.parse_activity(ordered_collection_data)
    assert isinstance(ordered_collection, ap.OerderedCollection)
    assert ordered_collection.id == "https://example.com/ordered-collection/1"

    # Restore backend
    ap.use_backend(None)


def test_actor_activities():
    back = InMemBackend()
    ap.use_backend(back)

    # Test Service activity
    service_data = {
        "type": "Service",
        "id": "https://example.com/service/1",
        "name": "Test Service",
    }

    service = ap.parse_activity(service_data)
    assert isinstance(service, ap.Service)
    assert service.id == "https://example.com/service/1"
    assert service.name == "Test Service"

    # Test Application activity
    application_data = {
        "type": "Application",
        "id": "https://example.com/app/1",
        "name": "Test Application",
    }

    application = ap.parse_activity(application_data)
    assert isinstance(application, ap.Application)
    assert application.id == "https://example.com/app/1"
    assert application.name == "Test Application"

    # Test Group activity
    group_data = {
        "type": "Group",
        "id": "https://example.com/group/1",
        "name": "Test Group",
    }

    group = ap.parse_activity(group_data)
    assert isinstance(group, ap.Group)
    assert group.id == "https://example.com/group/1"
    assert group.name == "Test Group"

    # Restore backend
    ap.use_backend(None)


def test_block_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Add the actor to the mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test Block activity
    block_data = {
        "type": "Block",
        "id": "https://example.com/block/1",
        "actor": "https://example.com/person/1",
        "object": "https://example.com/person/2",
    }

    block = ap.parse_activity(block_data)
    assert isinstance(block, ap.Block)
    assert block.id == "https://example.com/block/1"
    assert block.actor == "https://example.com/person/1"
    assert block.object == "https://example.com/person/2"

    # Restore backend
    ap.use_backend(None)


def test_article_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Test Article activity
    article_data = {
        "type": "Article",
        "id": "https://example.com/article/1",
        "content": "This is a test article",
        "attributedTo": "https://example.com/person/1",
    }

    article = ap.parse_activity(article_data)
    assert isinstance(article, ap.Article)
    assert article.id == "https://example.com/article/1"
    assert article.content == "This is a test article"
    assert article.attributedTo == "https://example.com/person/1"

    # Restore backend
    ap.use_backend(None)


def test_like_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Add the actor to the mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
    }

    # Test Like activity
    like_data = {
        "type": "Like",
        "id": "https://example.com/like/1",
        "actor": "https://example.com/person/1",
        "object": "https://example.com/note/1",
    }

    like = ap.parse_activity(like_data)
    assert isinstance(like, ap.Like)
    assert like.id == "https://example.com/like/1"
    assert like.actor == "https://example.com/person/1"
    assert like.object == "https://example.com/note/1"

    # Restore backend
    ap.use_backend(None)


def test_announce_activity():
    back = InMemBackend()
    ap.use_backend(back)

    # Add the actor to the mock data
    back.FETCH_MOCK["https://example.com/person/1"] = {
        "type": "Person",
        "id": "https://example.com/person/1",
        "name": "Test User",
        "preferredUsername": "testuser",
        "inbox": "https://example.com/person/1/inbox",
        "outbox": "https://example.com/person/1/outbox",
        "followers": "https://example.com/person/1/followers",
    }

    # Test Announce activity
    announce_data = {
        "type": "Announce",
        "id": "https://example.com/announce/1",
        "actor": "https://example.com/person/1",
        "object": "https://example.com/note/1",
        "to": [ap.AS_PUBLIC],
        "cc": [
            "https://example.com/person/1/followers",
            "https://example.com/person/2",
        ],
    }

    announce = ap.parse_activity(announce_data)
    assert isinstance(announce, ap.Announce)
    assert announce.id == "https://example.com/announce/1"
    assert announce.actor == "https://example.com/person/1"
    assert announce.object == "https://example.com/note/1"

    # Restore backend
    ap.use_backend(None)
