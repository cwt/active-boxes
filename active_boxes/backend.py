"""Async backend abstraction for ActivityPub.

This module provides the Backend base class for ActivityPub federation.
All network I/O is async using aiohttp.
"""

import abc
import asyncio
import binascii
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .http_client import check_url, get_http_client
from .__version__ import __version__
from .collection import parse_collection
from .errors import ActivityGoneError
from .errors import ActivityNotFoundError
from .errors import ActivityUnavailableError
from .errors import NotAnActivityError
from .urlutils import URLLookupFailedError

if TYPE_CHECKING:
    from active_boxes import activitypub as ap


class Backend(abc.ABC):
    """Abstract base class for ActivityPub backends.

    This class provides async network I/O methods for the library.
    Apps should subclass this and implement the abstract methods,
    or implement the ActivityPubPlugin protocol.
    """

    def debug_mode(self) -> bool:
        """Override to enable debug mode."""
        return False

    async def check_url(self, url: str) -> None:
        """Check if a URL is valid and accessible."""
        await check_url(url, debug=self.debug_mode())

    def user_agent(self) -> str:
        return f"Active Boxes/{__version__}; +http://github.com/tsileo/little-boxes)"

    def random_object_id(self) -> str:
        """Generate a random object ID."""
        return binascii.hexlify(os.urandom(8)).decode("utf-8")

    async def fetch_json_async(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch JSON from a URL asynchronously.

        Args:
            url: The URL to fetch
            **kwargs: Additional arguments passed to aiohttp

        Returns:
            Parsed JSON response
        """
        await self.check_url(url)

        client = await get_http_client()
        headers = {
            "User-Agent": self.user_agent(),
            "Accept": "application/activity+json, application/json",
        }
        headers.update(kwargs.pop("headers", {}))

        resp = await client.get_json(url, headers=headers, **kwargs)
        return resp

    def fetch_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch JSON from a URL (sync wrapper).

        For async code, use await fetch_json_async() instead.
        """
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Cannot use sync fetch_json from async context. "
                    "Use await fetch_json_async() instead."
                )
        except RuntimeError:
            pass
        return asyncio.run(self.fetch_json_async(url, **kwargs))

    def parse_collection(
        self,
        payload: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
    ) -> List[Any]:
        """Parse a Collection/OrderedCollection."""
        return parse_collection(
            payload=payload, url=url, fetcher=self.fetch_iri
        )

    def extra_inboxes(self) -> List[str]:
        """Return extra inboxes for every activity delivery.

        Override to add additional recipients (e.g., shared inboxes).
        """
        return []

    def is_from_outbox(
        self, as_actor: "ap.Person", activity: "ap.BaseActivity"
    ) -> bool:
        """Check if an activity originated from an actor's outbox."""
        return activity.get_actor().id == as_actor.id

    @abc.abstractmethod
    def base_url(self) -> str:
        """Return the application's base URL."""
        pass

    async def fetch_iri_async(self, iri: str, **kwargs) -> "ap.ObjectType":
        """Async: Fetch an IRI/URL and return parsed ActivityPub object.

        Args:
            iri: The IRI/URL to fetch
            **kwargs: Additional arguments

        Returns:
            ActivityPub object dict
        """
        if not iri.startswith("http"):
            raise NotAnActivityError(f"{iri} is not a valid IRI")

        try:
            await self.check_url(iri)
        except URLLookupFailedError:
            raise ActivityUnavailableError(
                f"unable to fetch {iri}, url lookup failed"
            )

        try:
            client = await get_http_client()
            headers = {
                "User-Agent": self.user_agent(),
                "Accept": "application/activity+json, application/json",
            }

            resp = await client.get_json(iri, headers=headers, **kwargs)
            return resp

        except ActivityNotFoundError:
            raise
        except ActivityGoneError:
            raise
        except ActivityUnavailableError:
            raise
        except Exception as e:
            raise ActivityUnavailableError(
                f"unable to fetch {iri}, unknown error: {e}"
            )

    def fetch_iri(self, iri: str, **kwargs) -> "ap.ObjectType":
        """Fetch an IRI/URL (sync wrapper).

        For async code, use await fetch_iri_async() instead.
        This method automatically handles calling async backends from sync code.
        """
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Cannot use sync fetch_iri from async context. "
                    "Use await fetch_iri_async() instead."
                )
        except RuntimeError:
            pass

        result = self.fetch_iri_async(iri, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result

    @abc.abstractmethod
    def activity_url(self, obj_id: str) -> str:
        """Return URL for an activity with the given ID."""
        pass

    @abc.abstractmethod
    def note_url(self, obj_id: str) -> str:
        """Return URL for a note with the given ID."""
        pass


class AsyncBackend(Backend):
    """A fully async Backend implementation.

    This backend uses aiohttp for all HTTP operations.
    Apps can subclass this for a ready-to-use async backend.
    """

    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch JSON using the global HTTP client."""
        return await self.fetch_json_async(url, **kwargs)

    async def post_json(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """POST JSON to a URL.

        Args:
            url: Target URL
            data: JSON data to send
            headers: Optional additional headers

        Returns:
            Response data
        """
        await self.check_url(url)

        client = await get_http_client()
        json_headers = {
            "User-Agent": self.user_agent(),
            "Content-Type": "application/activity+json",
            "Accept": "application/activity+json",
        }
        if headers:
            json_headers.update(headers)

        resp = await client.post_json(url, data, headers=json_headers)
        return resp
