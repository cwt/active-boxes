"""Regression tests for nested _sync wrappers inside a driven coroutine.

Repro (minimal, no app code): fetch_remote_activity_sync() on any Create
raised RuntimeError: Cannot run async code from within an async context,
because fetch_remote_activity_sync -> asyncio.run -> parse_activity ->
Create._init (unconditional get_object_sync) -> _run_sync sees the running
loop and raises. Same for await fetch_remote_activity(Create).

These tests use a stub backend and cover sync, async, and sync-inside-async
drivers.
"""

import asyncio

import pytest
from test_backend import InMemBackend

import active_boxes.activitypub as ap
from active_boxes._sync import _run_sync


@pytest.fixture
def stub_backend():
    back = InMemBackend()
    ap.use_backend(back)
    alice = back.setup_actor("Alice", "alice")
    yield back, alice
    ap.use_backend(None)


def _make_create(back, alice, cid="https://example.com/create/1"):
    note_dict = {
        "id": "https://example.com/note/1",
        "type": "Note",
        "attributedTo": alice.id,
        "content": "hello",
        "to": [ap.AS_PUBLIC],
    }
    create_dict = {
        "id": cid,
        "type": "Create",
        "actor": alice.id,
        "object": note_dict,
        "to": [ap.AS_PUBLIC],
    }
    back.FETCH_MOCK[cid] = create_dict
    return create_dict


def test_fetch_remote_activity_sync_create_nested(stub_backend):
    """Sync wrapper starts a loop, Create._init nests another _run_sync."""
    back, alice = stub_backend
    create_dict = _make_create(back, alice)
    act = ap.fetch_remote_activity_sync(create_dict["id"])
    assert isinstance(act, ap.Create)
    assert act.get_object_sync().content == "hello"


@pytest.mark.asyncio
async def test_fetch_remote_activity_create_async(stub_backend):
    """Async fetch must not fail in Create._init's sync wrapper."""
    back, alice = stub_backend
    create_dict = _make_create(back, alice)
    act = await ap.fetch_remote_activity(create_dict["id"])
    assert isinstance(act, ap.Create)
    obj = await act.get_object()
    assert obj.content == "hello"


def test_parse_create_inside_running_loop(stub_backend):
    """parse_activity(Create) inside asyncio.run (Flask eager-task shape)."""
    back, alice = stub_backend
    create_dict = _make_create(back, alice)

    async def driver():
        # Called from within a running loop, _init uses _sync wrappers.
        return ap.parse_activity(create_dict)

    act = asyncio.run(driver())
    assert isinstance(act, ap.Create)


def test_sync_wrapper_inside_running_loop(stub_backend):
    """fetch_remote_activity_sync called from inside a running loop."""
    back, alice = stub_backend
    create_dict = _make_create(back, alice)

    async def driver():
        return ap.fetch_remote_activity_sync(create_dict["id"])

    act = asyncio.run(driver())
    assert isinstance(act, ap.Create)


@pytest.mark.asyncio
async def test_run_sync_nest_safe():
    """Direct _run_sync from async context drives worker thread."""

    async def dummy():
        return 42

    assert _run_sync(dummy()) == 42


def test_create_with_iri_object(stub_backend):
    """Create referencing object by IRI must not crash _init on str."""
    back, alice = stub_backend
    note = ap.Note(
        content="remote",
        attributedTo=alice.id,
        to=[ap.AS_PUBLIC],
        id="https://example.com/note/remote1",
    )
    back.FETCH_MOCK[note.id] = note.to_dict()
    cid = "https://example.com/create/remote1"
    back.FETCH_MOCK[cid] = {
        "id": cid,
        "type": "Create",
        "actor": alice.id,
        "object": note.id,
        "to": [ap.AS_PUBLIC],
    }
    act = ap.fetch_remote_activity_sync(cid)
    assert isinstance(act, ap.Create)
