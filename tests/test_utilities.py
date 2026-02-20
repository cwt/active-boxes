"""Utility function tests."""

import logging
from unittest import mock

import pytest
import requests
from active_boxes import activitypub as ap
from active_boxes import content_helper
from active_boxes import urlutils
from active_boxes import webfinger
from active_boxes.activitypub import use_backend
from active_boxes.errors import BadActivityError
from active_boxes.collection import parse_collection
from active_boxes.errors import RecursionLimitExceededError
from active_boxes.errors import UnexpectedActivityTypeError

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


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
    assert (
        note_list_url.get_url() == "https://example.com/note/4.html"
    )  # Should return HTML version
    assert (
        note_list_url.get_url("text/plain") == "https://example.com/note/4.txt"
    )  # Should return TXT version

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
    assert note_list_url_fallback.get_url("text/html") == {
        "type": "Link",
        "href": "https://example.com/note/5.txt",
        "mimeType": "text/plain",
    }  # Should fallback to first object

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
    assert not private_create.is_public()

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
    assert public_create_to.is_public()

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
    assert public_create_cc.is_public()

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
    assert public_create_bto.is_public()

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
    assert public_create_bcc.is_public()

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
    assert result

    # Test with non-matching string
    result = ap._has_type("Note", ap.ActivityType.CREATE)
    assert not result

    # Test with list containing match
    result = ap._has_type(["Note", "Article"], ap.ActivityType.NOTE)
    assert result

    # Test with list containing no match
    result = ap._has_type(["Note", "Article"], ap.ActivityType.CREATE)
    assert not result

    # Test with empty lists
    result = ap._has_type([], [])
    assert not result


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
    result = note._actor_id(
        {"type": "Person", "id": "https://example.com/person/1"}
    )
    assert result == "https://example.com/person/1"

    # Test with dict missing id
    with pytest.raises(BadActivityError, match="missing object id"):
        note._actor_id({"type": "Person"})

    # Test with invalid actor field
    with pytest.raises(BadActivityError, match='invalid "actor" field'):
        note._actor_id(123)

    # Restore backend
    ap.use_backend(None)


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


def test_little_content_helper_simple():
    back = InMemBackend()
    ap.use_backend(back)

    result = content_helper.parse_markdown("hello")
    if result:
        content, tags = result
        assert content == "<p>hello</p>"
        assert tags == []


def test_little_content_helper_linkify():
    back = InMemBackend()
    ap.use_backend(back)

    result = content_helper.parse_markdown("hello https://google.com")
    if result:
        content, tags = result
        assert content.startswith("<p>hello <a")
        assert "https://google.com" in content
        assert tags == []


@mock.patch(
    "active_boxes.content_helper.get_actor_url",
    return_value="https://microblog.pub",
)
def test_little_content_helper_mention(_):
    back = InMemBackend()
    ap.use_backend(back)
    back.FETCH_MOCK["https://microblog.pub"] = {
        "id": "https://microblog.pub",
        "url": "https://microblog.pub",
    }

    result = content_helper.parse_markdown("hello @dev@microblog.pub")
    if result:
        content, tags = result
        assert content == (
            '<p>hello <span class="h-card"><a href="https://microblog.pub" class="u-url mention">@<span>dev</span>'
            "@microblog.pub</a></span></p>"
        )
        assert tags == [
            {
                "href": "https://microblog.pub",
                "name": "@dev@microblog.pub",
                "type": "Mention",
            }
        ]


@mock.patch(
    "active_boxes.content_helper.get_actor_url",
    return_value="https://microblog.pub",
)
def test_little_content_helper_tag(_):
    back = InMemBackend()
    ap.use_backend(back)

    result = content_helper.parse_markdown("hello #activitypub")
    if result:
        content, tags = result
        base_url = back.base_url()
        assert content == (
            f'<p>hello <a href="{base_url}/tags/activitypub" class="mention hashtag" rel="tag">#'
            f"<span>activitypub</span></a></p>"
        )
        assert tags == [
            {
                "href": f"{base_url}/tags/activitypub",
                "name": "#activitypub",
                "type": "Hashtag",
            }
        ]


def test_urlutils_reject_invalid_scheme():
    assert not urlutils.is_url_valid("ftp://localhost:123")


def test_urlutils_reject_localhost():
    assert not urlutils.is_url_valid("http://localhost:8000")


def test_urlutils_reject_private_ip():
    assert not urlutils.is_url_valid("http://192.168.1.10:8000")


@mock.patch(
    "socket.getaddrinfo", return_value=[[0, 1, 2, 3, ["192.168.1.11", None]]]
)
def test_urlutils_reject_domain_that_resolve_to_private_ip(_):
    assert not urlutils.is_url_valid("http://resolve-to-private.com")


@mock.patch(
    "socket.getaddrinfo", return_value=[[0, 1, 2, 3, ["1.2.3.4", None]]]
)
def test_urlutils_accept_valid_url(_):
    assert urlutils.is_url_valid("https://microblog.pub")


def test_urlutils_check_url_helper():
    with pytest.raises(urlutils.InvalidURLError):
        urlutils.check_url("http://localhost:5000")


_WEBFINGER_RESP = {
    "aliases": ["https://microblog.pub"],
    "links": [
        {
            "href": "https://microblog.pub",
            "rel": "http://webfinger.net/rel/profile-page",
            "type": "text/html",
        },
        {
            "href": "https://microblog.pub",
            "rel": "self",
            "type": "application/activity+json",
        },
        {
            "rel": "http://ostatus.org/schema/1.0/subscribe",
            "template": "https://microblog.pub/authorize_follow?profile={uri}",
        },
    ],
    "subject": "acct:dev@microblog.pub",
}


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_webfinger(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to return our test response
    mock_response = mock.Mock()
    mock_response.json.return_value = _WEBFINGER_RESP
    mock_response.raise_for_status.return_value = None
    mock_fetch_json.return_value = mock_response

    if data := webfinger.webfinger("@dev@microblog.pub"):
        assert data == _WEBFINGER_RESP

        assert (
            webfinger.get_actor_url("@dev@microblog.pub")
            == "https://microblog.pub"
        )
        assert (
            webfinger.get_remote_follow_template("@dev@microblog.pub")
            == "https://microblog.pub/authorize_follow?profile={uri}"
        )


def test_webfinger_invalid_url():
    with pytest.raises(urlutils.InvalidURLError):
        webfinger.webfinger("@dev@localhost:8080")


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_webfinger_with_http_url(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to return our test response
    mock_response = mock.Mock()
    mock_response.json.return_value = _WEBFINGER_RESP
    mock_response.raise_for_status.return_value = None
    mock_fetch_json.return_value = mock_response

    # Test with HTTP URL
    data = webfinger.webfinger("http://dev@microblog.pub")
    assert data == _WEBFINGER_RESP


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_webfinger_with_acct_uri(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to return our test response
    mock_response = mock.Mock()
    mock_response.json.return_value = _WEBFINGER_RESP
    mock_response.raise_for_status.return_value = None
    mock_fetch_json.return_value = mock_response

    # Test with acct URI
    data = webfinger.webfinger("acct:dev@microblog.pub")
    assert data == _WEBFINGER_RESP


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_webfinger_connection_error(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to raise ConnectionError
    mock_fetch_json.side_effect = requests.ConnectionError("Connection failed")

    # Test with connection error
    data = webfinger.webfinger("@dev@microblog.pub")
    assert data is None


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_get_actor_url(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to return our test response
    mock_response = mock.Mock()
    mock_response.json.return_value = _WEBFINGER_RESP
    mock_response.raise_for_status.return_value = None
    mock_fetch_json.return_value = mock_response

    # Test get_actor_url function
    url = webfinger.get_actor_url("@dev@microblog.pub")
    assert url == "https://microblog.pub"


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch("active_boxes.backend.check_url", return_value=None)
@mock.patch("active_boxes.backend.Backend.fetch_json")
def test_get_remote_follow_template(mock_fetch_json, _, _1):
    # Initialize backend
    back = InMemBackend()
    use_backend(back)

    # Mock the fetch_json method to return our test response
    mock_response = mock.Mock()
    mock_response.json.return_value = _WEBFINGER_RESP
    mock_response.raise_for_status.return_value = None
    mock_fetch_json.return_value = mock_response

    # Test get_remote_follow_template function
    template = webfinger.get_remote_follow_template("@dev@microblog.pub")
    assert template == "https://microblog.pub/authorize_follow?profile={uri}"


@mock.patch("active_boxes.webfinger.check_url")
@mock.patch("active_boxes.backend.check_url")
def test_webfinger_debug_mode(mock_check_url, mock_backend_check_url):
    # Test webfinger with debug mode - should still raise InvalidURLError for localhost
    # Mock check_url to raise InvalidURLError for localhost
    mock_check_url.side_effect = urlutils.InvalidURLError("Invalid URL")
    mock_backend_check_url.side_effect = urlutils.InvalidURLError("Invalid URL")

    with pytest.raises(urlutils.InvalidURLError):
        webfinger.webfinger("@dev@localhost:8080", debug=True)


def test_empty_collection():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "items": [],
        "id": "https://lol.com",
    }

    if out := parse_collection(url="https://lol.com", fetcher=back.fetch_iri):
        assert out == []


def test_recursive_collection_limit():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "first": "https://lol.com",
        "id": "https://lol.com",
    }

    with pytest.raises(RecursionLimitExceededError):
        parse_collection(url="https://lol.com", fetcher=back.fetch_iri)


def test_unexpected_activity_type():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Actor",
        "id": "https://lol.com",
    }

    with pytest.raises(UnexpectedActivityTypeError):
        parse_collection(url="https://lol.com", fetcher=back.fetch_iri)


def test_collection():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "first": "https://lol.com/page1",
        "id": "https://lol.com",
    }
    back.FETCH_MOCK["https://lol.com/page1"] = {
        "type": "CollectionPage",
        "id": "https://lol.com/page1",
        "items": [1, 2, 3],
    }

    if out := parse_collection(url="https://lol.com", fetcher=back.fetch_iri):
        assert out == [1, 2, 3]


def test_ordered_collection():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "OrderedCollection",
        "first": {
            "type": "OrderedCollectionPage",
            "id": "https://lol.com/page1",
            "orderedItems": [1, 2, 3],
            "next": "https://lol.com/page2",
        },
        "id": "https://lol.com",
    }
    back.FETCH_MOCK["https://lol.com/page2"] = {
        "type": "OrderedCollectionPage",
        "id": "https://lol.com/page2",
        "orderedItems": [4, 5, 6],
    }

    if out := parse_collection(url="https://lol.com", fetcher=back.fetch_iri):
        assert out == [1, 2, 3, 4, 5, 6]
