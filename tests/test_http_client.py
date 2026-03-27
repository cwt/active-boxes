"""Tests for http_client module."""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest import mock

import aiohttp
import pytest

from active_boxes import activitypub as ap
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
async def test_fetch_json():
    with mock.patch.object(http_client, "AsyncHTTPClient") as MockClient:
        mock_instance = mock.Mock()
        mock_instance.get_json = mock.AsyncMock(return_value={"test": "data"})
        mock_instance.close = mock.AsyncMock()
        MockClient.return_value = mock_instance

        result = await http_client.fetch_json("https://example.com")
        assert result == {"test": "data"}
        mock_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_activity():
    with mock.patch.object(http_client, "fetch_json") as mock_fetch:
        mock_fetch.return_value = {
            "type": "Create",
            "id": "https://example.com/act",
        }
        result = await http_client.fetch_activity("https://example.com")
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


# Additional tests for http_client module coverage
class TestRunSync:
    """Test _run_sync helper function."""

    def test_run_sync_non_coroutine(self):
        """Test _run_sync with non-coroutine value."""
        result = http_client._run_sync(42)
        assert result == 42

    def test_run_sync_with_string(self):
        """Test _run_sync with string."""
        result = http_client._run_sync("hello")
        assert result == "hello"

    def test_run_sync_with_none(self):
        """Test _run_sync with None."""
        result = http_client._run_sync(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_run_sync_from_async_raises(self):
        """Test _run_sync raises from async context."""

        async def dummy():
            return 1

        coro = dummy()
        with pytest.raises(RuntimeError, match="Cannot run async code"):
            http_client._run_sync(coro)
        # Clean up the coroutine if not consumed
        try:
            await coro
        except RuntimeError:
            pass

    def test_run_sync_from_sync(self):
        """Test _run_sync works from sync context."""

        async def dummy():
            return "success"

        result = http_client._run_sync(dummy())
        assert result == "success"


class TestCheckUrl:
    """Test check_url functions."""

    @pytest.mark.asyncio
    async def test_check_url_async_valid(self):
        """Test async check_url with valid URL."""
        await http_client.check_url("https://example.com")

    def test_check_url_sync_valid(self):
        """Test sync check_url with valid URL."""
        http_client.check_url_sync("https://example.com")

    @pytest.mark.asyncio
    async def test_check_url_async_invalid(self):
        """Test async check_url with invalid URL."""
        from active_boxes.urlutils import InvalidURLError

        with pytest.raises(InvalidURLError):
            await http_client.check_url("not-a-url")

    def test_check_url_sync_invalid(self):
        """Test sync check_url with invalid URL."""
        from active_boxes.urlutils import InvalidURLError

        with pytest.raises(InvalidURLError):
            http_client.check_url_sync("not-a-url")


class TestFetchJson:
    """Test fetch_json functions."""

    @pytest.mark.asyncio
    async def test_fetch_json_with_custom_user_agent(self):
        """Test fetch_json with custom user agent."""
        with mock.patch.object(http_client, "AsyncHTTPClient") as MockClient:
            mock_instance = mock.Mock()
            mock_instance.get_json = mock.AsyncMock(return_value={"data": 1})
            mock_instance.close = mock.AsyncMock()
            MockClient.return_value = mock_instance

            result = await http_client.fetch_json(
                "https://example.com", user_agent="CustomAgent/1.0"
            )
            assert result == {"data": 1}

    @pytest.mark.asyncio
    async def test_fetch_json_with_custom_timeout(self):
        """Test fetch_json with custom timeout."""
        with mock.patch.object(http_client, "AsyncHTTPClient") as MockClient:
            mock_instance = mock.Mock()
            mock_instance.get_json = mock.AsyncMock(return_value={"data": 1})
            mock_instance.close = mock.AsyncMock()
            MockClient.return_value = mock_instance

            result = await http_client.fetch_json(
                "https://example.com", timeout=30
            )
            assert result == {"data": 1}
            # Verify AsyncHTTPClient was created with custom timeout
            MockClient.assert_called_once_with(timeout=30)

    def test_fetch_json_sync(self):
        """Test fetch_json_sync wrapper."""
        with mock.patch.object(http_client, "fetch_json") as mock_fetch:
            mock_fetch.return_value = {"sync": "data"}
            result = http_client.fetch_json_sync("https://example.com")
            assert result == {"sync": "data"}


class TestFetchActivity:
    """Test fetch_activity functions."""

    @pytest.mark.asyncio
    async def test_fetch_activity_with_custom_params(self):
        """Test fetch_activity with custom user agent and timeout."""
        with mock.patch.object(http_client, "fetch_json") as mock_fetch:
            mock_fetch.return_value = {
                "type": "Note",
                "id": "https://example.com/note/1",
            }

            result = await http_client.fetch_activity(
                "https://example.com/note/1",
                user_agent="TestAgent/1.0",
                timeout=20,
            )
            assert result["type"] == "Note"
            mock_fetch.assert_called_once_with(
                "https://example.com/note/1",
                user_agent="TestAgent/1.0",
                timeout=20,
            )

    def test_fetch_activity_sync(self):
        """Test fetch_activity_sync wrapper."""
        with mock.patch.object(http_client, "fetch_activity") as mock_fetch:
            mock_fetch.return_value = {"type": "Create"}
            result = http_client.fetch_activity_sync("https://example.com")
            assert result["type"] == "Create"


class TestAsyncHTTPClient:
    """Test AsyncHTTPClient class."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test AsyncHTTPClient initialization."""
        client = http_client.AsyncHTTPClient(timeout=30)
        assert client.timeout == 30
        assert client._session is None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_creates_session(self):
        """Test _get_session creates new session."""
        client = http_client.AsyncHTTPClient()
        session = await client._get_session()
        assert session is not None
        assert client._session is session
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self):
        """Test _get_session reuses existing session."""
        client = http_client.AsyncHTTPClient()
        session1 = await client._get_session()
        session2 = await client._get_session()
        assert session1 is session2
        await client.close()

    @pytest.mark.asyncio
    async def test_close_with_no_session(self):
        """Test close when no session exists."""
        client = http_client.AsyncHTTPClient()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_get_json_404_error(self):
        """Test get_json raises ActivityUnavailableError on 404 (wrapped from ActivityNotFoundError)."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            # Create a proper async context manager mock
            mock_resp = mock.AsyncMock()
            mock_resp.status = 404
            mock_resp.raise_for_status = mock.Mock()

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value = mock_resp
            mock_cm.__aexit__.return_value = None

            with mock.patch.object(session, "get", return_value=mock_cm):
                # Note: ActivityNotFoundError gets caught and re-raised as ActivityUnavailableError
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/missing")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_410_error(self):
        """Test get_json raises ActivityUnavailableError on 410 (wrapped from ActivityGoneError)."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_resp = mock.AsyncMock()
            mock_resp.status = 410

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value = mock_resp
            mock_cm.__aexit__.return_value = None

            with mock.patch.object(session, "get", return_value=mock_cm):
                # Note: ActivityGoneError gets caught and re-raised as ActivityUnavailableError
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/gone")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_500_error(self):
        """Test get_json raises ActivityUnavailableError on 500."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value.status = 500

            with mock.patch.object(session, "get", return_value=mock_cm):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/error")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_502_error(self):
        """Test get_json raises ActivityUnavailableError on 502."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value.status = 502

            with mock.patch.object(session, "get", return_value=mock_cm):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/error")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_503_error(self):
        """Test get_json raises ActivityUnavailableError on 503."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value.status = 503

            with mock.patch.object(session, "get", return_value=mock_cm):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/error")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_invalid_json(self):
        """Test get_json raises ActivityUnavailableError on invalid JSON response."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_cm = mock.AsyncMock()
            mock_cm.__aenter__.return_value.status = 200
            mock_cm.__aenter__.return_value.raise_for_status = mock.Mock()
            mock_cm.__aenter__.return_value.json = mock.AsyncMock(
                side_effect=Exception("Invalid JSON")
            )

            with mock.patch.object(session, "get", return_value=mock_cm):
                # Note: NotAnActivityError gets caught and re-raised as ActivityUnavailableError
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/invalid")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_connection_error(self):
        """Test get_json raises ActivityUnavailableError on connection error."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            with mock.patch.object(
                session,
                "get",
                side_effect=aiohttp.ClientConnectorError(
                    mock.Mock(), mock.Mock()
                ),
            ):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/error")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_timeout(self):
        """Test get_json raises ActivityUnavailableError on timeout."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            with mock.patch.object(
                session, "get", side_effect=asyncio.TimeoutError()
            ):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.get_json("https://example.com/timeout")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_json_custom_timeout(self):
        """Test get_json with custom timeout."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_response = mock.AsyncMock()
            mock_response.status = 200
            mock_response.raise_for_status = mock.Mock()
            mock_response.json = mock.AsyncMock(return_value={"data": 1})

            with mock.patch.object(session, "get") as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await client.get_json(
                    "https://example.com/data", timeout=30
                )
                assert result == {"data": 1}

            await client.close()

    @pytest.mark.asyncio
    async def test_post_json_success(self):
        """Test post_json successful POST."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_response = mock.AsyncMock()
            mock_response.status = 200

            async def mock_post(*args, **kwargs):
                return mock_response

            with mock.patch.object(
                session, "post", side_effect=mock_post
            ) as mock_post_func:
                result = await client.post_json(
                    "https://example.com/inbox", {"test": "data"}
                )
                assert result is mock_response
                mock_post_func.assert_called_once()

            await client.close()

    @pytest.mark.asyncio
    async def test_post_json_with_headers(self):
        """Test post_json with custom headers."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            mock_response = mock.AsyncMock()

            async def mock_post(*args, **kwargs):
                return mock_response

            with mock.patch.object(
                session, "post", side_effect=mock_post
            ) as mock_post_func:
                await client.post_json(
                    "https://example.com/inbox",
                    {"test": "data"},
                    headers={"X-Custom": "header"},
                )

                # Verify headers were passed
                call_kwargs = mock_post_func.call_args[1]
                assert "headers" in call_kwargs

            await client.close()

    @pytest.mark.asyncio
    async def test_post_json_connection_error(self):
        """Test post_json raises ActivityUnavailableError on connection error."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            with mock.patch.object(
                session,
                "post",
                side_effect=aiohttp.ClientConnectorError(
                    mock.Mock(), mock.Mock()
                ),
            ):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.post_json("https://example.com/inbox", {})

            await client.close()

    @pytest.mark.asyncio
    async def test_post_json_timeout(self):
        """Test post_json raises ActivityUnavailableError on timeout."""
        with mock.patch.object(http_client, "check_url"):
            client = http_client.AsyncHTTPClient()
            session = await client._get_session()

            with mock.patch.object(
                session, "post", side_effect=asyncio.TimeoutError()
            ):
                with pytest.raises(ap.ActivityUnavailableError):
                    await client.post_json("https://example.com/inbox", {})

            await client.close()


class TestHeaderHelpers:
    """Test header helper functions."""

    def test_get_accept_header_all_types(self):
        """Test get_accept_header with all supported types."""
        assert (
            http_client.get_accept_header("activity")
            == "application/activity+json"
        )
        assert "application/ld+json" in http_client.get_accept_header("ld_json")
        assert http_client.get_accept_header("json") == "application/json"
        assert http_client.get_accept_header("html") == "text/html"
        assert http_client.get_accept_header("any") == "*/*"
        # Unknown type defaults to activity
        assert (
            http_client.get_accept_header("unknown")
            == "application/activity+json"
        )

    def test_get_content_type_header_all_types(self):
        """Test get_content_type_header with all supported types."""
        assert (
            http_client.get_content_type_header("activity")
            == "application/activity+json"
        )
        assert (
            http_client.get_content_type_header("ld_json")
            == "application/ld+json"
        )
        assert http_client.get_content_type_header("json") == "application/json"
        # Unknown type defaults to activity
        assert (
            http_client.get_content_type_header("unknown")
            == "application/activity+json"
        )

    def test_build_csp_header_basic(self):
        """Test build_csp_header basic functionality."""
        headers = http_client.build_csp_header("https://example.com")
        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        csp = headers["Content-Security-Policy"]
        assert "https://example.com" in csp
        assert "/.well-known/webfinger" in csp

    def test_build_csp_header_no_webfinger(self):
        """Test build_csp_header without webfinger."""
        headers = http_client.build_csp_header(
            "https://example.com", include_webfinger=False
        )
        csp = headers["Content-Security-Policy"]
        assert "/.well-known/webfinger" not in csp

    def test_build_csp_header_no_stream(self):
        """Test build_csp_header without stream."""
        headers = http_client.build_csp_header(
            "https://example.com", include_stream=False
        )
        csp = headers["Content-Security-Policy"]
        assert "/stream/*" not in csp

    def test_build_activity_headers(self):
        """Test build_activity_headers."""
        headers = http_client.build_activity_headers("https://example.com")
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers

    def test_build_activity_headers_custom_types(self):
        """Test build_activity_headers with custom types."""
        headers = http_client.build_activity_headers(
            "https://example.com", content_type="json", accept_type="json"
        )
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"


class TestVerifyDateHeader:
    """Test verify_date_header function."""

    def test_verify_date_header_valid(self):
        """Test verify_date_header with valid recent date."""
        from email.utils import format_datetime
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        date_str = format_datetime(now)
        assert http_client.verify_date_header(date_str) is True

    def test_verify_date_header_expired(self):
        """Test verify_date_header with old date."""
        from email.utils import format_datetime
        from datetime import datetime, timezone

        old = datetime.now(timezone.utc) - timedelta(hours=1)
        date_str = format_datetime(old)
        assert http_client.verify_date_header(date_str) is False

    def test_verify_date_header_none(self):
        """Test verify_date_header with None."""
        assert http_client.verify_date_header(None) is False

    def test_verify_date_header_invalid_format(self):
        """Test verify_date_header with invalid format."""
        assert http_client.verify_date_header("not-a-date") is False


class TestComputeDigest:
    """Test compute_digest function."""

    def test_compute_digest_basic(self):
        """Test compute_digest with basic input."""
        digest = http_client.compute_digest("test body")
        assert digest.startswith("SHA-256=")
        assert len(digest) > 10  # Should have actual hash

    def test_compute_digest_empty(self):
        """Test compute_digest with empty string."""
        digest = http_client.compute_digest("")
        assert digest.startswith("SHA-256=")

    def test_compute_digest_unicode(self):
        """Test compute_digest with unicode content."""
        digest = http_client.compute_digest("Hello 世界")
        assert digest.startswith("SHA-256=")
