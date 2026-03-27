"""Collection related utilities for ActivityPub.

This module provides functions for parsing and navigating ActivityPub
Collections and OrderedCollections, including support for backward
pagination via the `prev` link.
"""

import asyncio
import inspect
from typing import Any, AsyncIterator, Dict, List, Optional, Callable
from dataclasses import dataclass

from .errors import RecursionLimitExceededError, UnexpectedActivityTypeError


@dataclass
class CollectionPage:
    """Represents a single page of a Collection."""

    items: List[Any]
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
    part_of: Optional[str] = None
    total_items: Optional[int] = None
    id: Optional[str] = None
    type: str = "CollectionPage"


class CollectionPaginator:
    """Async paginator for ActivityPub Collections.

    Supports forward pagination (via `next` link) and backward
    pagination (via `prev` link), as well as `first`/`last` links.
    """

    def __init__(
        self,
        fetcher: Callable[[str], Any],
        max_depth: int = 3,
        page_size: Optional[int] = None,
    ) -> None:
        """Initialize the paginator.

        Args:
            fetcher: Async function to fetch a URL and return JSON dict
            max_depth: Maximum recursion depth for following links
            page_size: Optional page size limit per page
        """
        self.fetcher = fetcher
        self.max_depth = max_depth
        self.page_size = page_size

    async def _fetch(self, url: str) -> Dict[str, Any]:
        """Fetch a URL using the async fetcher."""
        if inspect.iscoroutinefunction(self.fetcher):
            return await self.fetcher(url)
        else:
            return await asyncio.to_thread(self.fetcher, url)

    async def get_first_page(
        self, collection: Dict[str, Any]
    ) -> CollectionPage:
        """Get the first page of a collection.

        Args:
            collection: A Collection or OrderedCollection dict

        Returns:
            CollectionPage with items from the first page
        """
        if collection["type"] in ["Collection", "OrderedCollection"]:
            if "orderedItems" in collection:
                return CollectionPage(
                    items=collection["orderedItems"],
                    total_items=collection.get("totalItems"),
                    id=collection.get("id"),
                    type=collection["type"],
                )
            if "items" in collection:
                return CollectionPage(
                    items=collection["items"],
                    total_items=collection.get("totalItems"),
                    id=collection.get("id"),
                    type=collection["type"],
                )

            first = collection.get("first")
            if isinstance(first, str):
                first_data = await self._fetch(first)
                return self._parse_page(first_data, first)
            elif isinstance(first, dict):
                return self._parse_page(first, collection.get("id"))

        elif collection["type"] in ["CollectionPage", "OrderedCollectionPage"]:
            return self._parse_page(collection)

        raise UnexpectedActivityTypeError(
            f"unexpected collection type: {collection['type']}"
        )

    def _parse_page(
        self, page: Dict[str, Any], part_of: Optional[str] = None
    ) -> CollectionPage:
        """Parse a collection page dict into a CollectionPage object."""
        items = page.get("orderedItems") or page.get("items") or []
        if self.page_size:
            items = items[: self.page_size]

        return CollectionPage(
            items=items,
            next_url=page.get("next"),
            prev_url=page.get("prev"),
            part_of=page.get("partOf") or part_of,
            total_items=page.get("totalItems"),
            id=page.get("id"),
            type=page["type"],
        )

    async def get_page(self, url: str) -> CollectionPage:
        """Fetch and parse a specific page URL."""
        data = await self._fetch(url)
        return self._parse_page(data)

    async def iterate_forward(
        self, collection: Dict[str, Any]
    ) -> AsyncIterator[Any]:
        """Iterate forward through all pages via `next` links.

        Args:
            collection: A Collection or OrderedCollection dict

        Yields:
            Items from each page
        """
        page = await self.get_first_page(collection)
        for item in page.items:
            yield item

        depth = 1
        while page.next_url and depth < self.max_depth:
            page = await self.get_page(page.next_url)
            for item in page.items:
                yield item
            depth += 1

    async def iterate_backward(
        self, collection: Dict[str, Any]
    ) -> AsyncIterator[Any]:
        """Iterate backward through pages via `prev` links.

        Note: This requires the server to support `prev` links,
        which is not required by the ActivityPub spec but is
        implemented by some servers.

        Args:
            collection: A Collection or OrderedCollection dict

        Yields:
            Items from each page in reverse order
        """
        if "last" not in collection and "prev" not in collection:
            return

        if "last" in collection:
            last_url = collection["last"]
            if isinstance(last_url, str):
                page = await self.get_page(last_url)
            else:
                page = self._parse_page(last_url, collection.get("id"))
        else:
            page = await self.get_first_page(collection)
            if not page.prev_url:
                return

        depth = 1
        while page and depth < self.max_depth:
            for item in reversed(page.items):
                yield item

            if not page.prev_url:
                break
            page = await self.get_page(page.prev_url)
            depth += 1

    async def get_all_items(
        self, collection: Dict[str, Any], direction: str = "forward"
    ) -> List[Any]:
        """Get all items from a collection.

        Args:
            collection: A Collection or OrderedCollection dict
            direction: "forward" or "backward"

        Returns:
            List of all items in the collection
        """
        items = []
        if direction == "forward":
            async for item in self.iterate_forward(collection):
                items.append(item)
        else:
            async for item in self.iterate_backward(collection):
                items.append(item)
        return items

    def validate_part_of(
        self, page: CollectionPage, expected_base: str
    ) -> bool:
        """Validate that a page's partOf matches the expected base URL.

        Args:
            page: CollectionPage to validate
            expected_base: Expected base URL

        Returns:
            True if valid, False otherwise
        """
        if not page.part_of:
            return True
        return page.part_of == expected_base or page.part_of.startswith(
            f"{expected_base}?"
        )


async def parse_collection(
    payload: Optional[Dict[str, Any]] = None,
    url: Optional[str] = None,
    level: int = 0,
    fetcher: Optional[Callable[[str], Any]] = None,
    max_depth: int = 3,
) -> List[Any]:
    """Resolve/fetch a Collection/OrderedCollection (async).

    Args:
        payload: Optional collection dict
        url: Optional URL to fetch
        level: Current recursion depth
        fetcher: Async function to fetch URLs
        max_depth: Maximum recursion depth

    Returns:
        List of items from the collection
    """
    if not fetcher:
        raise ValueError("must provide a fetcher")
    if level > max_depth:
        raise RecursionLimitExceededError("recursion limit exceeded")

    if inspect.iscoroutinefunction(fetcher):
        fetch = fetcher
    else:

        async def fetch(url):
            return await asyncio.to_thread(fetcher, url)

    out: List[Any] = []
    if url:
        payload = await fetch(url)
    if not payload:
        raise ValueError("must provide at least a payload or URL")

    if payload["type"] in ["Collection", "OrderedCollection"]:
        if "orderedItems" in payload:
            return payload["orderedItems"]
        if "items" in payload:
            return payload["items"]
        if "first" in payload:
            if isinstance(payload["first"], str):
                out.extend(
                    await parse_collection(
                        url=payload["first"],
                        level=level + 1,
                        fetcher=fetch,
                        max_depth=max_depth,
                    )
                )
            else:
                if "orderedItems" in payload["first"]:
                    out.extend(payload["first"]["orderedItems"])
                if "items" in payload["first"]:
                    out.extend(payload["first"]["items"])
                if n := payload["first"].get("next"):
                    out.extend(
                        await parse_collection(
                            url=n,
                            level=level + 1,
                            fetcher=fetch,
                            max_depth=max_depth,
                        )
                    )
        return out

    while payload:
        if payload["type"] in ["CollectionPage", "OrderedCollectionPage"]:
            if "orderedItems" in payload:
                out.extend(payload["orderedItems"])
            if "items" in payload:
                out.extend(payload["items"])

            if "prev" in payload:
                break

            if (n := payload.get("next")) is None:
                break
            payload = await fetch(n)
        else:
            raise UnexpectedActivityTypeError(
                f"unexpected activity type {payload['type']}"
            )

    return out


def parse_collection_sync(
    payload: Optional[Dict[str, Any]] = None,
    url: Optional[str] = None,
    level: int = 0,
    fetcher: Optional[Callable[[str], Any]] = None,
    max_depth: int = 3,
) -> List[Any]:
    """Resolve/fetch a Collection/OrderedCollection (sync).

    For async code, use await parse_collection() instead.

    Args:
        payload: Optional collection dict
        url: Optional URL to fetch
        level: Current recursion depth
        fetcher: Sync function to fetch URLs
        max_depth: Maximum recursion depth

    Returns:
        List of items from the collection
    """
    if not fetcher:
        raise ValueError("must provide a fetcher")
    if level > max_depth:
        raise RecursionLimitExceededError("recursion limit exceeded")

    out: List[Any] = []
    if url:
        payload = fetcher(url)
    if not payload:
        raise ValueError("must provide at least a payload or URL")

    if payload["type"] in ["Collection", "OrderedCollection"]:
        if "orderedItems" in payload:
            return payload["orderedItems"]
        if "items" in payload:
            return payload["items"]
        if "first" in payload:
            if isinstance(payload["first"], str):
                out.extend(
                    parse_collection_sync(
                        url=payload["first"],
                        level=level + 1,
                        fetcher=fetcher,
                        max_depth=max_depth,
                    )
                )
            else:
                if "orderedItems" in payload["first"]:
                    out.extend(payload["first"]["orderedItems"])
                if "items" in payload["first"]:
                    out.extend(payload["first"]["items"])
                if n := payload["first"].get("next"):
                    out.extend(
                        parse_collection_sync(
                            url=n,
                            level=level + 1,
                            fetcher=fetcher,
                            max_depth=max_depth,
                        )
                    )
        return out

    while payload:
        if payload["type"] in ["CollectionPage", "OrderedCollectionPage"]:
            if "orderedItems" in payload:
                out.extend(payload["orderedItems"])
            if "items" in payload:
                out.extend(payload["items"])

            if "prev" in payload:
                break

            if (n := payload.get("next")) is None:
                break
            payload = fetcher(n)
        else:
            raise UnexpectedActivityTypeError(
                f"unexpected activity type {payload['type']}"
            )

    return out
