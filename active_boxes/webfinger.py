"""WebFinger support for ActivityPub.

This module provides WebFinger endpoint discovery for ActivityPub actors.
"""

import asyncio
import logging
from typing import Any, Dict
from urllib.parse import urlparse

from .activitypub import _maybe_await
from .activitypub import get_backend_async
from .urlutils import check_url

logger = logging.getLogger(__name__)


async def webfinger_async(
    resource: str, debug: bool = False
) -> Dict[str, Any] | None:
    """Async version: Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL."""
    logger.info(f"performing webfinger resolution for {resource}")
    protos = ["https", "http"]
    if resource.startswith("http://"):
        protos.reverse()
        host = urlparse(resource).netloc
    elif resource.startswith("https://"):
        host = urlparse(resource).netloc
    else:
        if resource.startswith("acct:"):
            resource = resource[5:]
        if resource.startswith("@"):
            resource = resource[1:]
        _, host = resource.split("@", 1)
        resource = "acct:" + resource

    check_url(f"https://{host}", debug=debug)
    resp = None

    backend = await get_backend_async()

    for i, proto in enumerate(protos):
        try:
            url = f"{proto}://{host}/.well-known/webfinger"
            result = backend.fetch_json(url, params={"resource": resource})
            resp = await _maybe_await(result)
            return resp
        except Exception:
            logger.exception("fetch failed")
            if i == 0:
                continue
            break

    return None


def webfinger(resource: str, debug: bool = False) -> Dict[str, Any] | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL.

    For async code, use await webfinger_async() instead.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(webfinger_async(resource, debug))

    return loop.run_until_complete(webfinger_async(resource, debug))


async def get_remote_follow_template_async(
    resource: str, debug: bool = False
) -> str | None:
    """Async version: Get the remote follow template for a resource."""
    data = await webfinger_async(resource, debug)
    if not data:
        return None
    for link in data["links"]:
        if link.get("rel") == "http://ostatus.org/schema/1.0/subscribe":
            return link.get("template")
    return None


def get_remote_follow_template(
    resource: str, debug: bool = False
) -> str | None:
    """Get the remote follow template for a resource."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(get_remote_follow_template_async(resource, debug))

    return loop.run_until_complete(
        get_remote_follow_template_async(resource, debug)
    )


async def get_actor_url_async(resource: str, debug: bool = False) -> str | None:
    """Async version: Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL.

    Returns:
        the Actor URL or None if the resolution failed.
    """
    data = await webfinger_async(resource, debug)
    if not data:
        return None
    for link in data["links"]:
        if (
            link.get("rel") == "self"
            and link.get("type") == "application/activity+json"
        ):
            return link.get("href")
    return None


def get_actor_url(resource: str, debug: bool = False) -> str | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL.

    Returns:
        the Actor URL or None if the resolution failed.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(get_actor_url_async(resource, debug))

    return loop.run_until_complete(get_actor_url_async(resource, debug))
