"""WebFinger support for ActivityPub.

This module provides WebFinger endpoint discovery for ActivityPub actors.
"""

import asyncio
import logging
from typing import Any, Dict
from urllib.parse import urlparse

from .activitypub import _await_if_coroutine
from .activitypub import get_backend
from .urlutils import check_url

logger = logging.getLogger(__name__)


def _run_sync(coro):
    """Run an async coroutine from sync code.

    This enables Flask/Django and other sync frameworks to use the library.
    For new code, prefer async/await syntax.

    Args:
        coro: A coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        RuntimeError: If called from within an async context
    """
    if not asyncio.iscoroutine(coro):
        return coro

    try:
        asyncio.get_running_loop()
        raise RuntimeError(
            "Cannot run async code from within an async context. "
            "Use 'await' instead of the _sync() wrapper."
        )
    except RuntimeError as e:
        if "no running event loop" in str(e):
            return asyncio.run(coro)
        raise


async def webfinger(
    resource: str, debug: bool = False
) -> Dict[str, Any] | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL (async).

    Args:
        resource: The resource to resolve (e.g., @user@example.com or acct:user@example.com)
        debug: Enable debug mode

    Returns:
        WebFinger response dict or None if resolution failed
    """
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

    backend = get_backend()

    for i, proto in enumerate(protos):
        try:
            url = f"{proto}://{host}/.well-known/webfinger"
            result = backend.fetch_json(url, params={"resource": resource})
            resp = await _await_if_coroutine(result)
            return resp
        except Exception:
            logger.exception("fetch failed")
            if i == 0:
                continue
            break

    return None


def webfinger_sync(resource: str, debug: bool = False) -> Dict[str, Any] | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL (sync).

    For async code, use await webfinger() instead.

    Args:
        resource: The resource to resolve
        debug: Enable debug mode

    Returns:
        WebFinger response dict or None if resolution failed
    """
    return _run_sync(webfinger(resource, debug))


async def get_remote_follow_template(
    resource: str, debug: bool = False
) -> str | None:
    """Get the remote follow template for a resource (async).

    Args:
        resource: The resource to resolve
        debug: Enable debug mode

    Returns:
        Remote follow template URL or None
    """
    data = await webfinger(resource, debug)
    if not data:
        return None
    for link in data["links"]:
        if link.get("rel") == "http://ostatus.org/schema/1.0/subscribe":
            return link.get("template")
    return None


def get_remote_follow_template_sync(
    resource: str, debug: bool = False
) -> str | None:
    """Get the remote follow template for a resource (sync).

    For async code, use await get_remote_follow_template() instead.
    """
    return _run_sync(get_remote_follow_template(resource, debug))


async def get_actor_url(resource: str, debug: bool = False) -> str | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL (async).

    Args:
        resource: The resource to resolve
        debug: Enable debug mode

    Returns:
        the Actor URL or None if the resolution failed.
    """
    data = await webfinger(resource, debug)
    if not data:
        return None
    for link in data["links"]:
        if (
            link.get("rel") == "self"
            and link.get("type") == "application/activity+json"
        ):
            return link.get("href")
    return None


def get_actor_url_sync(resource: str, debug: bool = False) -> str | None:
    """Mastodon-like WebFinger resolution to retrieve the activity stream Actor URL (sync).

    For async code, use await get_actor_url() instead.

    Args:
        resource: The resource to resolve
        debug: Enable debug mode

    Returns:
        the Actor URL or None if the resolution failed.
    """
    return _run_sync(get_actor_url(resource, debug))
