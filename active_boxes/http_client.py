"""Async HTTP client utilities for ActivityPub.

This module provides async HTTP functionality for the library,
replacing the synchronous requests-based implementation.
"""

import asyncio
import base64
import hashlib
import logging
import time
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp

from .__version__ import __version__
from .errors import ActivityGoneError
from .errors import ActivityNotFoundError
from .errors import ActivityUnavailableError
from .errors import NotAnActivityError
from .urlutils import check_url as sync_check_url

logger = logging.getLogger(__name__)


async def check_url(url: str, debug: bool = False) -> None:
    """Async version of URL validation."""
    await asyncio.to_thread(sync_check_url, url, debug=debug)


class AsyncHTTPClient:
    """Async HTTP client for ActivityPub requests.

    Provides async versions of HTTP operations needed for
    ActivityPub federation, including proper signature support.
    """

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch JSON from a URL.

        Args:
            url: The URL to fetch
            headers: Optional HTTP headers
            timeout: Optional timeout override

        Returns:
            Parsed JSON response

        Raises:
            ActivityNotFoundError: 404 response
            ActivityGoneError: 410 response
            ActivityUnavailableError: 5xx response or connection error
        """
        await check_url(url)

        session = await self._get_session()
        if timeout is None:
            timeout = self.timeout

        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
            ) as resp:
                if resp.status == 404:
                    raise ActivityNotFoundError(f"{url} is not found")
                elif resp.status == 410:
                    raise ActivityGoneError(f"{url} is gone")
                elif resp.status in (500, 502, 503):
                    raise ActivityUnavailableError(
                        f"unable to fetch {url}, server error ({resp.status})"
                    )

                resp.raise_for_status()

                try:
                    return await resp.json()
                except Exception as e:
                    raise NotAnActivityError(f"{url} is not JSON: {e}")

        except aiohttp.ClientConnectorError as e:
            raise ActivityUnavailableError(
                f"unable to fetch {url}, connection error: {e}"
            )
        except asyncio.TimeoutError:
            raise ActivityUnavailableError(f"unable to fetch {url}, timeout")
        except Exception as e:
            raise ActivityUnavailableError(
                f"unable to fetch {url}, unknown error: {e}"
            )

    async def post_json(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> aiohttp.ClientResponse:
        """POST JSON to a URL.

        Args:
            url: The URL to POST to
            data: JSON-serializable data to send
            headers: Optional HTTP headers
            timeout: Optional timeout override

        Returns:
            The response object

        Raises:
            ActivityUnavailableError: On connection/timeout errors
        """
        await check_url(url)

        session = await self._get_session()
        if timeout is None:
            timeout = self.timeout

        json_headers = dict(headers or {})
        json_headers.setdefault("Content-Type", "application/json")
        json_headers.setdefault("Accept", "application/activity+json")

        try:
            resp = await session.post(
                url,
                json=data,
                headers=json_headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            )
            return resp
        except aiohttp.ClientConnectorError as e:
            raise ActivityUnavailableError(
                f"unable to POST to {url}, connection error: {e}"
            )
        except asyncio.TimeoutError:
            raise ActivityUnavailableError(f"unable to POST to {url}, timeout")
        except Exception as e:
            raise ActivityUnavailableError(
                f"unable to POST to {url}, unknown error: {e}"
            )


async def fetch_json_async(
    url: str,
    user_agent: Optional[str] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Standalone async function to fetch JSON from a URL.

    Args:
        url: The URL to fetch
        user_agent: Optional user agent string
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response
    """
    if user_agent is None:
        user_agent = f"Active Boxes/{__version__}"

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/activity+json, application/json",
    }

    client = AsyncHTTPClient(timeout=timeout)
    try:
        return await client.get_json(url, headers=headers)
    finally:
        await client.close()


async def fetch_activity_async(
    url: str,
    user_agent: Optional[str] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Fetch an ActivityPub activity/object from a URL.

    Args:
        url: The URL to fetch
        user_agent: Optional user agent string
        timeout: Request timeout in seconds

    Returns:
        Activity dict
    """
    return await fetch_json_async(url, user_agent=user_agent, timeout=timeout)


def verify_date_header(
    date_str: Optional[str], max_age_seconds: int = 300
) -> bool:
    """Verify Date header for replay attack prevention.

    Args:
        date_str: The Date header value (e.g., "Fri, 27 Mar 2026 12:00:00 GMT")
        max_age_seconds: Maximum acceptable age in seconds (default 5 minutes)

    Returns:
        True if the date is fresh and within acceptable range
    """
    if not date_str:
        return False

    try:
        from email.utils import parsedate_to_datetime

        date = parsedate_to_datetime(date_str)
        now = time.time()
        date_timestamp = date.timestamp()
        age = abs(now - date_timestamp)
        return age <= max_age_seconds
    except (ValueError, TypeError):
        return False


def compute_digest(body: str) -> str:
    """Compute SHA-256 digest for HTTP Signature.

    Args:
        body: The request body string

    Returns:
        Digest header value (e.g., "SHA-256=abc123...")
    """
    h = hashlib.sha256()
    h.update(body.encode("utf-8"))
    return "SHA-256=" + base64.b64encode(h.digest()).decode("utf-8")


_http_client: Optional[AsyncHTTPClient] = None


async def get_http_client() -> AsyncHTTPClient:
    """Get the global async HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = AsyncHTTPClient()
    return _http_client


async def close_http_client() -> None:
    """Close the global HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None


ACCEPT_HEADERS = {
    "activity": "application/activity+json",
    "ld_json": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    "json": "application/json",
    "html": "text/html",
    "any": "*/*",
}

CONTENT_TYPE_HEADERS = {
    "activity": "application/activity+json",
    "ld_json": "application/ld+json",
    "json": "application/json",
}


def get_accept_header(accept_type: str = "activity") -> str:
    """Get the Accept header value for content negotiation.

    Args:
        accept_type: One of "activity", "ld_json", "json", "html", or "any"

    Returns:
        Accept header value
    """
    return ACCEPT_HEADERS.get(accept_type, ACCEPT_HEADERS["activity"])


def get_content_type_header(content_type: str = "activity") -> str:
    """Get the Content-Type header value.

    Args:
        content_type: One of "activity", "ld_json", or "json"

    Returns:
        Content-Type header value
    """
    return CONTENT_TYPE_HEADERS.get(
        content_type, CONTENT_TYPE_HEADERS["activity"]
    )


def build_csp_header(
    base_url: str,
    include_webfinger: bool = True,
    include_stream: bool = True,
) -> Dict[str, str]:
    """Build Content Security Policy headers for ActivityPub.

    Args:
        base_url: The application's base URL
        include_webfinger: Whether to include WebFinger endpoint
        include_stream: Whether to include stream endpoints

    Returns:
        Dict of headers to include in response
    """
    csp = [
        "default-src 'none'",
        f"base {base_url}",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "media-src 'self'",
        "img-src 'self' data: https:",
        "font-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "script-src 'self'",
    ]

    if include_webfinger:
        csp.append("/.well-known/webfinger 'self'")

    if include_stream:
        csp.append(f"{base_url}/stream/* 'self'")

    return {
        "Content-Security-Policy": "; ".join(csp),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }


def build_activity_headers(
    base_url: str,
    content_type: str = "activity",
    accept_type: str = "activity",
) -> Dict[str, str]:
    """Build standard headers for ActivityPub requests/responses.

    Args:
        base_url: The application's base URL
        content_type: Content-Type for requests
        accept_type: Accept type for requests

    Returns:
        Dict of headers
    """
    headers = {
        "Accept": get_accept_header(accept_type),
        "Content-Type": get_content_type_header(content_type),
    }
    headers.update(build_csp_header(base_url))
    return headers
