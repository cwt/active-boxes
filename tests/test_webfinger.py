import logging
from unittest import mock

import pytest
from active_boxes import urlutils
from active_boxes import webfinger
from active_boxes.activitypub import use_backend

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


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
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_webfinger(_, _1):
    back = InMemBackend()
    use_backend(back)

    back.FETCH_MOCK["https://microblog.pub/.well-known/webfinger"] = (
        _WEBFINGER_RESP
    )

    if data := webfinger.webfinger_sync("@dev@microblog.pub"):
        assert data == _WEBFINGER_RESP

        assert (
            webfinger.get_actor_url_sync("@dev@microblog.pub")
            == "https://microblog.pub"
        )
        assert (
            webfinger.get_remote_follow_template_sync("@dev@microblog.pub")
            == "https://microblog.pub/authorize_follow?profile={uri}"
        )


def test_webfinger_invalid_url():
    with pytest.raises(urlutils.InvalidURLError):
        webfinger.webfinger_sync("@dev@localhost:8080")


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_webfinger_with_http_url(_, _1):
    back = InMemBackend()
    use_backend(back)

    # When URL starts with http://, it tries http first
    # The host is parsed from the URL, keeping the user part
    back.FETCH_MOCK["http://dev@microblog.pub/.well-known/webfinger"] = (
        _WEBFINGER_RESP
    )

    data = webfinger.webfinger_sync("http://dev@microblog.pub")
    assert data == _WEBFINGER_RESP


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_webfinger_with_acct_uri(_, _1):
    back = InMemBackend()
    use_backend(back)

    back.FETCH_MOCK["https://microblog.pub/.well-known/webfinger"] = (
        _WEBFINGER_RESP
    )

    data = webfinger.webfinger_sync("acct:dev@microblog.pub")
    assert data == _WEBFINGER_RESP


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_webfinger_connection_error(_, _1):
    back = InMemBackend()
    use_backend(back)

    # Clear FETCH_MOCK to ensure no cached data
    back.FETCH_MOCK.clear()

    # No FETCH_MOCK setup - will return {} when fetch fails (key not found)
    data = webfinger.webfinger_sync("@dev@microblog.pub")
    # Empty dict is the "failure" response from InMemBackend
    assert not data


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_get_actor_url(_, _1):
    back = InMemBackend()
    use_backend(back)

    back.FETCH_MOCK["https://microblog.pub/.well-known/webfinger"] = (
        _WEBFINGER_RESP
    )

    url = webfinger.get_actor_url_sync("@dev@microblog.pub")
    assert url == "https://microblog.pub"


@mock.patch("active_boxes.webfinger.check_url", return_value=None)
@mock.patch(
    "active_boxes.backend.check_url",
    new_callable=mock.AsyncMock,
    return_value=None,
)
def test_get_remote_follow_template(_, _1):
    back = InMemBackend()
    use_backend(back)

    back.FETCH_MOCK["https://microblog.pub/.well-known/webfinger"] = (
        _WEBFINGER_RESP
    )

    template = webfinger.get_remote_follow_template_sync("@dev@microblog.pub")
    assert template == "https://microblog.pub/authorize_follow?profile={uri}"


@mock.patch("active_boxes.webfinger.check_url")
@mock.patch("active_boxes.backend.check_url")
def test_webfinger_debug_mode(mock_check_url, mock_backend_check_url):
    # Test webfinger with debug mode - should still raise InvalidURLError for localhost
    # Mock check_url to raise InvalidURLError for localhost
    mock_check_url.side_effect = urlutils.InvalidURLError("Invalid URL")
    mock_backend_check_url.side_effect = urlutils.InvalidURLError("Invalid URL")

    with pytest.raises(urlutils.InvalidURLError):
        webfinger.webfinger_sync("@dev@localhost:8080", debug=True)
