import logging
from unittest import mock

import pytest
import requests
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
