"""Tests for http_client module."""

from datetime import datetime, timezone
from unittest import mock

import pytest

from active_boxes import http_client


def test_verify_date_header_valid():
    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    assert http_client.verify_date_header(date_str) is True


def test_verify_date_header_expired():
    old_date = "Mon, 01 Jan 2020 00:00:00 GMT"
    assert http_client.verify_date_header(old_date) is False


def test_verify_date_header_none():
    assert http_client.verify_date_header(None) is False


def test_verify_date_header_invalid():
    assert http_client.verify_date_header("not a date") is False


def test_compute_digest():
    digest = http_client.compute_digest("test body")
    assert digest.startswith("SHA-256=")
    assert len(digest) > 10


def test_get_accept_header_activity():
    result = http_client.get_accept_header("activity")
    assert result == "application/activity+json"


def test_get_accept_header_ld_json():
    result = http_client.get_accept_header("ld_json")
    assert "application/ld+json" in result


def test_get_accept_header_json():
    result = http_client.get_accept_header("json")
    assert result == "application/json"


def test_get_accept_header_html():
    result = http_client.get_accept_header("html")
    assert result == "text/html"


def test_get_accept_header_any():
    result = http_client.get_accept_header("any")
    assert result == "*/*"


def test_get_accept_header_unknown():
    result = http_client.get_accept_header("unknown")
    assert result == "application/activity+json"


def test_get_content_type_header_activity():
    result = http_client.get_content_type_header("activity")
    assert result == "application/activity+json"


def test_get_content_type_header_ld_json():
    result = http_client.get_content_type_header("ld_json")
    assert result == "application/ld+json"


def test_get_content_type_header_json():
    result = http_client.get_content_type_header("json")
    assert result == "application/json"


def test_get_content_type_header_unknown():
    result = http_client.get_content_type_header("unknown")
    assert result == "application/activity+json"


def test_build_csp_header_basic():
    headers = http_client.build_csp_header(
        "https://example.com", include_webfinger=False, include_stream=False
    )
    assert "Content-Security-Policy" in headers
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers
    assert "https://example.com" in headers["Content-Security-Policy"]


def test_build_csp_header_with_webfinger():
    headers = http_client.build_csp_header(
        "https://example.com", include_webfinger=True, include_stream=False
    )
    assert "/.well-known/webfinger" in headers["Content-Security-Policy"]


def test_build_csp_header_with_stream():
    headers = http_client.build_csp_header(
        "https://example.com", include_webfinger=False, include_stream=True
    )
    assert "https://example.com/stream/*" in headers["Content-Security-Policy"]


def test_build_csp_header_full():
    headers = http_client.build_csp_header(
        "https://example.com", include_webfinger=True, include_stream=True
    )
    csp = headers["Content-Security-Policy"]
    assert "/.well-known/webfinger" in csp
    assert "https://example.com/stream/*" in csp


def test_build_activity_headers():
    headers = http_client.build_activity_headers("https://example.com")
    assert "Accept" in headers
    assert "Content-Type" in headers
    assert "Content-Security-Policy" in headers
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers


def test_build_activity_headers_custom_types():
    headers = http_client.build_activity_headers(
        "https://example.com", content_type="json", accept_type="json"
    )
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_check_url_valid():
    await http_client.check_url("https://example.com")


@pytest.mark.asyncio
async def test_check_url_invalid():
    from active_boxes.urlutils import InvalidURLError

    with pytest.raises(InvalidURLError):
        await http_client.check_url("not-a-url")


@pytest.mark.asyncio
async def test_fetch_json_async():
    with mock.patch.object(http_client, "AsyncHTTPClient") as MockClient:
        mock_instance = mock.Mock()
        mock_instance.get_json = mock.AsyncMock(return_value={"test": "data"})
        mock_instance.close = mock.AsyncMock()
        MockClient.return_value = mock_instance

        result = await http_client.fetch_json_async("https://example.com")
        assert result == {"test": "data"}
        mock_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_activity_async():
    with mock.patch.object(http_client, "fetch_json_async") as mock_fetch:
        mock_fetch.return_value = {
            "type": "Create",
            "id": "https://example.com/act",
        }
        result = await http_client.fetch_activity_async("https://example.com")
        assert result["type"] == "Create"


async def test_get_http_client_singleton():
    http_client._http_client = None
    client1 = await http_client.get_http_client()
    client2 = await http_client.get_http_client()
    assert client1 is client2
    await http_client.close_http_client()


async def test_close_http_client():
    http_client._http_client = None
    await http_client.get_http_client()
    await http_client.close_http_client()
    assert http_client._http_client is None
