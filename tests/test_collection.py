import logging

import pytest
from active_boxes import activitypub as ap
from active_boxes.collection import (
    CollectionPage,
    CollectionPaginator,
    parse_collection,
    parse_collection_async,
)
from active_boxes.errors import RecursionLimitExceededError
from active_boxes.errors import UnexpectedActivityTypeError

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


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


def test_collection_page_dataclass():
    page = CollectionPage(items=[1, 2, 3], next_url="https://lol.com/next")
    assert page.items == [1, 2, 3]
    assert page.next_url == "https://lol.com/next"
    assert page.type == "CollectionPage"


def test_collection_page_with_all_fields():
    page = CollectionPage(
        items=[1],
        next_url="https://lol.com/next",
        prev_url="https://lol.com/prev",
        part_of="https://lol.com",
        total_items=10,
        id="https://lol.com/page1",
        type="OrderedCollectionPage",
    )
    assert page.total_items == 10
    assert page.prev_url == "https://lol.com/prev"
    assert page.part_of == "https://lol.com"


@pytest.mark.asyncio
async def test_parse_collection_async_basic():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "items": [1, 2, 3],
        "id": "https://lol.com",
    }

    result = await parse_collection_async(
        url="https://lol.com", fetcher=back.fetch_iri_async
    )
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_parse_collection_async_with_payload():
    payload = {
        "type": "Collection",
        "orderedItems": [1, 2, 3],
        "id": "https://lol.com",
    }

    async def noop_fetcher(url):
        return {}

    result = await parse_collection_async(payload=payload, fetcher=noop_fetcher)
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_parse_collection_async_no_fetcher():
    with pytest.raises(ValueError, match="must provide a fetcher"):
        await parse_collection_async(
            payload={"type": "Collection", "items": []}
        )


@pytest.mark.asyncio
async def test_parse_collection_async_recursion_limit():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "first": "https://lol.com",
        "id": "https://lol.com",
    }

    with pytest.raises(RecursionLimitExceededError):
        await parse_collection_async(
            url="https://lol.com",
            fetcher=back.fetch_iri_async,
            max_depth=1,
        )


@pytest.mark.asyncio
async def test_parse_collection_async_first_string():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com"] = {
        "type": "Collection",
        "first": "https://lol.com/page1",
        "id": "https://lol.com",
    }
    back.FETCH_MOCK["https://lol.com/page1"] = {
        "type": "CollectionPage",
        "items": [1, 2],
        "id": "https://lol.com/page1",
    }

    result = await parse_collection_async(
        url="https://lol.com", fetcher=back.fetch_iri_async
    )
    assert result == [1, 2]


@pytest.mark.asyncio
async def test_parse_collection_async_first_dict():
    payload = {
        "type": "Collection",
        "first": {
            "type": "CollectionPage",
            "items": [1, 2],
            "id": "https://lol.com/page1",
        },
        "id": "https://lol.com",
    }

    async def noop_fetcher(url):
        return {}

    result = await parse_collection_async(payload=payload, fetcher=noop_fetcher)
    assert result == [1, 2]


@pytest.mark.asyncio
async def test_parse_collection_async_page_with_next():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com/page1"] = {
        "type": "CollectionPage",
        "items": [1, 2],
        "next": "https://lol.com/page2",
        "id": "https://lol.com/page1",
    }
    back.FETCH_MOCK["https://lol.com/page2"] = {
        "type": "CollectionPage",
        "items": [3, 4],
        "id": "https://lol.com/page2",
    }

    result = await parse_collection_async(
        url="https://lol.com/page1", fetcher=back.fetch_iri_async
    )
    assert result == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_parse_collection_async_page_with_prev():
    back = InMemBackend()
    ap.use_backend(back)

    back.FETCH_MOCK["https://lol.com/page1"] = {
        "type": "CollectionPage",
        "items": [1, 2],
        "prev": "https://lol.com/page0",
        "id": "https://lol.com/page1",
    }

    result = await parse_collection_async(
        url="https://lol.com/page1", fetcher=back.fetch_iri_async
    )
    assert result == [1, 2]


def test_collection_paginator_init():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher, max_depth=5, page_size=10)
    assert paginator.max_depth == 5
    assert paginator.page_size == 10


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_ordered_items():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "OrderedCollection",
        "orderedItems": [1, 2, 3],
        "totalItems": 3,
        "id": "https://lol.com",
    }

    page = await paginator.get_first_page(collection)
    assert page.items == [1, 2, 3]
    assert page.total_items == 3


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_items():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "Collection",
        "items": [1, 2, 3],
        "totalItems": 3,
        "id": "https://lol.com",
    }

    page = await paginator.get_first_page(collection)
    assert page.items == [1, 2, 3]


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_first_string():
    async def fetcher(url):
        return {
            "type": "CollectionPage",
            "items": [1, 2],
            "id": url,
        }

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "Collection",
        "first": "https://lol.com/page1",
        "id": "https://lol.com",
    }

    page = await paginator.get_first_page(collection)
    assert page.items == [1, 2]


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_first_dict():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "Collection",
        "first": {
            "type": "CollectionPage",
            "items": [1, 2],
            "id": "https://lol.com/page1",
        },
        "id": "https://lol.com",
    }

    page = await paginator.get_first_page(collection)
    assert page.items == [1, 2]


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_collection_page():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)
    page_data = {
        "type": "CollectionPage",
        "items": [1, 2],
        "id": "https://lol.com/page1",
    }

    page = await paginator.get_first_page(page_data)
    assert page.items == [1, 2]


@pytest.mark.asyncio
async def test_collection_paginator_get_first_page_unexpected_type():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "Actor",
        "id": "https://lol.com",
    }

    with pytest.raises(UnexpectedActivityTypeError):
        await paginator.get_first_page(collection)


@pytest.mark.asyncio
async def test_collection_paginator_get_page():
    async def fetcher(url):
        return {
            "type": "CollectionPage",
            "items": [1, 2],
            "id": url,
        }

    paginator = CollectionPaginator(fetcher)
    page = await paginator.get_page("https://lol.com/page1")
    assert page.items == [1, 2]


@pytest.mark.asyncio
async def test_collection_paginator_iterate_forward():
    page1_data = {
        "type": "CollectionPage",
        "items": [1, 2],
        "next": "https://lol.com/page2",
        "id": "https://lol.com/page1",
    }
    page2_data = {
        "type": "CollectionPage",
        "items": [3, 4],
        "id": "https://lol.com/page2",
    }

    async def fetcher(url):
        if url == "https://lol.com":
            return {
                "type": "Collection",
                "first": "https://lol.com/page1",
                "id": "https://lol.com",
            }
        return page1_data if "page1" in url else page2_data

    paginator = CollectionPaginator(fetcher, max_depth=3)
    collection = await fetcher("https://lol.com")

    items = []
    async for item in paginator.iterate_forward(collection):
        items.append(item)

    assert items == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_collection_paginator_iterate_backward_with_last():
    last_page = {
        "type": "CollectionPage",
        "items": [3, 4],
        "prev": "https://lol.com/page1",
        "id": "https://lol.com/last",
    }
    page1_data = {
        "type": "CollectionPage",
        "items": [1, 2],
        "id": "https://lol.com/page1",
    }

    async def fetcher(url):
        if url == "https://lol.com":
            return {
                "type": "Collection",
                "first": "https://lol.com/page1",
                "last": "https://lol.com/last",
                "id": "https://lol.com",
            }
        return page1_data if "page1" in url else last_page

    paginator = CollectionPaginator(fetcher, max_depth=3)
    collection = await fetcher("https://lol.com")

    items = []
    async for item in paginator.iterate_backward(collection):
        items.append(item)

    assert items == [4, 3, 2, 1]


@pytest.mark.asyncio
async def test_collection_paginator_iterate_backward_no_last_or_prev():
    async def fetcher(url):
        return {
            "type": "CollectionPage",
            "items": [1, 2],
            "id": "https://lol.com/page1",
        }

    paginator = CollectionPaginator(fetcher)
    collection = {
        "type": "Collection",
        "first": "https://lol.com/page1",
        "id": "https://lol.com",
    }

    items = []
    async for item in paginator.iterate_backward(collection):
        items.append(item)

    assert items == []


@pytest.mark.asyncio
async def test_collection_paginator_get_all_items_forward():
    async def fetcher(url):
        return {
            "type": "Collection",
            "first": "https://lol.com/page1",
            "id": "https://lol.com",
        }

    paginator = CollectionPaginator(fetcher, max_depth=3)
    collection = await fetcher("https://lol.com")

    items = await paginator.get_all_items(collection, direction="forward")
    assert items == []


def test_collection_paginator_validate_part_of():
    async def fetcher(url):
        return {}

    paginator = CollectionPaginator(fetcher)

    page = CollectionPage(items=[1], part_of="https://lol.com?page=1")
    assert paginator.validate_part_of(page, "https://lol.com") is True

    page2 = CollectionPage(items=[1], part_of="https://other.com")
    assert paginator.validate_part_of(page2, "https://lol.com") is False

    page3 = CollectionPage(items=[1], part_of=None)
    assert paginator.validate_part_of(page3, "https://lol.com") is True


def test_collection_paginator_page_size():
    async def fetcher(url):
        return {
            "type": "CollectionPage",
            "items": [1, 2, 3, 4, 5],
            "id": url,
        }

    paginator = CollectionPaginator(fetcher, page_size=3)
    page = paginator._parse_page(
        {"type": "CollectionPage", "items": [1, 2, 3, 4, 5]}
    )
    assert len(page.items) == 3
