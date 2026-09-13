"""Nest-safe sync bridge for async code.

This module provides a single shared implementation of ``_run_sync`` used by
all ``*_sync`` wrappers (Flask/Django and other sync frameworks).

Behavior:
- Fast path: when the calling thread has no running event loop, run the
  coroutine inline with :func:`asyncio.run`.
- Nested path: when the calling thread already runs an event loop (e.g.
  ``fetch_remote_activity_sync`` -> ``asyncio.run`` -> ``parse_activity``
  -> ``Create._init`` -> ``get_object_sync``, or any ``*_sync`` wrapper
  called from within a driven coroutine), drive the coroutine to completion
  in a dedicated worker thread with its own fresh event loop and block the
  caller waiting for the result.

Each nesting level blocks only its own thread waiting on a child thread,
so there is no deadlock. Flask behavior is unchanged for the common
single-level case.
"""

import asyncio
import concurrent.futures


def _run_sync(coro):
    """Run an async coroutine from sync code (nest-safe).

    This enables Flask/Django and other sync frameworks to use the library.
    For new async code, prefer ``await`` syntax.

    Args:
        coro: A coroutine to run (non-coroutines are returned as-is).

    Returns:
        The result of the coroutine.
    """
    if not asyncio.iscoroutine(coro):
        return coro

    try:
        asyncio.get_running_loop()
    except RuntimeError as exc:
        if "no running event loop" in str(exc):
            # No event loop running in this thread, safe to use asyncio.run().
            return asyncio.run(coro)
        raise

    # A loop is already running in this thread: run the coroutine in a
    # dedicated worker thread with a fresh loop and wait for it.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()
