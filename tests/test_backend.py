import json
from typing import List
from typing import Optional
from unittest import mock

import pytest

import active_boxes.activitypub as ap
from active_boxes.backend import Backend, AsyncBackend, _run_sync


def track_call(f):
    """Method decorator used to track the events fired during tests."""
    fname = f.__name__

    def wrapper(*args, **kwargs):
        args[0]._METHOD_CALLS[args[1].id].append((fname, args, kwargs))
        return f(*args, **kwargs)

    return wrapper


class InMemBackend(Backend):
    """In-memory backend meant to be used for the test suite."""

    DB: dict[str, dict[str, list]] = {}
    USERS: dict[str, ap.Person] = {}
    FETCH_MOCK: dict[str, ap.ObjectType] = {}
    INBOX_IDX: dict[str, dict] = {}
    OUTBOX_IDX: dict[str, dict] = {}
    FOLLOWERS: dict[str, list] = {}
    FOLLOWING: dict[str, list] = {}

    _METHOD_CALLS: dict[str, list] = {}

    def called_methods(self, p: ap.Person) -> List[str]:
        data = list(self._METHOD_CALLS[p.id])
        self._METHOD_CALLS[p.id] = []
        return data

    def assert_called_methods(self, p: ap.Person, *asserts) -> List[str]:
        calls = self.called_methods(p)
        for i, assert_data in enumerate(asserts):
            if len(calls) < i + 1:
                raise ValueError(f"no methods called at step #{i}")
            error_msg, name, *funcs = assert_data
            if name != calls[i][0]:
                raise ValueError(
                    f"expected method {name} to be called at step #{i}, but got {calls[i][0]}"
                )
            if len(funcs) < len(calls[i][1]) - 1:
                raise ValueError(
                    f"args left unchecked for method {name} at step #{i}"
                )
            for z, f in enumerate(funcs):
                if len(calls[i][1]) < z + 2:
                    raise ValueError(f"method {name} has no args at index {z}")
                try:
                    f(calls[i][1][z + 1])
                except AssertionError as ae:
                    ae.args = ((error_msg),)
                    raise ae

        if len(asserts) < len(calls):
            raise ValueError(
                f"expecting {len(calls)} assertion, only got {len(asserts)},"
                f"leftover: {calls[len(asserts) :]!r}"
            )

        return calls

    def debug_mode(self) -> bool:
        return True

    def setup_actor(self, name, pusername):
        """Create a new actor in this backend."""
        if p := ap.Person(
            name=name,
            preferredUsername=pusername,
            summary="Hello",
            id=f"https://lol.com/{pusername}",
            inbox=f"https://lol.com/{pusername}/inbox",
            followers=f"https://lol.com/{pusername}/followers",
            following=f"https://lol.com/{pusername}/following",
        ):
            self.USERS[p.preferredUsername] = p
            self.DB[p.id] = {"inbox": [], "outbox": []}
            self.INBOX_IDX[p.id] = {}
            self.OUTBOX_IDX[p.id] = {}
            self.FOLLOWERS[p.id] = []
            self.FOLLOWING[p.id] = []
            self.FETCH_MOCK[p.id] = p.to_dict()
            self._METHOD_CALLS[p.id] = []
            return p

    async def fetch_iri(self, iri: str, **kwargs) -> ap.ObjectType:
        """Async fetch for in-memory backend."""
        return self._fetch_iri_sync(iri)

    async def fetch_json(self, url: str, **kwargs) -> dict:
        """Async fetch_json for webfinger support."""
        return self.FETCH_MOCK.get(url, {})

    def fetch_iri_sync(self, iri: str, **kwargs) -> ap.ObjectType:
        """Sync fetch for in-memory backend."""
        return self._fetch_iri_sync(iri)

    def _fetch_iri_sync(self, iri: str) -> ap.ObjectType:
        """Synchronous fetch implementation for in-memory backend."""
        match iri:
            case iri if iri.endswith("/followers"):
                data = self.FOLLOWERS[iri.replace("/followers", "")]
                return {
                    "id": iri,
                    "type": ap.ActivityType.ORDERED_COLLECTION.value,
                    "totalItems": len(data),
                    "orderedItems": data,
                }
            case iri if iri.endswith("/following"):
                data = self.FOLLOWING[iri.replace("/following", "")]
                return {
                    "id": iri,
                    "type": ap.ActivityType.ORDERED_COLLECTION.value,
                    "totalItems": len(data),
                    "orderedItems": data,
                }
            case _:
                return self.FETCH_MOCK[iri]

    def get_user(self, username: str) -> ap.Person:
        if username in self.USERS:
            return self.USERS[username]
        else:
            raise ValueError(f"bad username {username}")

    @track_call
    def outbox_is_blocked(self, as_actor: ap.Person, actor_id: str) -> bool:
        """Returns True if `as_actor` has blocked `actor_id`."""
        for activity in self.DB[as_actor.id]["outbox"]:
            if activity.ACTIVITY_TYPE == ap.ActivityType.BLOCK:
                return True
        return False

    def inbox_check_duplicate(
        self, as_actor: ap.Person, iri: str
    ) -> Optional[ap.BaseActivity]:
        for activity in self.DB[as_actor.id]["inbox"]:
            if activity.id == iri:
                return activity

        return None

    @track_call
    def inbox_new(self, as_actor: ap.Person, activity: ap.BaseActivity) -> None:
        if activity.id in self.INBOX_IDX[as_actor.id]:
            return
        self.DB[as_actor.id]["inbox"].append(activity)
        self.INBOX_IDX[as_actor.id][activity.id] = activity

    def base_url(self) -> str:
        return "https://todo"

    def activity_url(self, obj_id: str) -> str:
        # from the random hex ID
        return f"https://todo/{obj_id}"

    def note_url(self, obj_id: str) -> str:
        # from the random hex ID
        return f"https://todo/note/{obj_id}"

    @track_call
    def outbox_new(
        self, as_actor: ap.Person, activity: ap.BaseActivity
    ) -> None:
        print(f"saving {activity!r} to DB")
        actor_id = activity.get_actor_sync().id
        if activity.id in self.OUTBOX_IDX[actor_id]:
            return
        self.DB[actor_id]["outbox"].append(activity)
        self.OUTBOX_IDX[actor_id][activity.id] = activity
        self.FETCH_MOCK[activity.id] = activity.to_dict()
        if isinstance(activity, ap.Create):
            self.FETCH_MOCK[activity.get_object_sync().id] = (
                activity.get_object_sync().to_dict()
            )

    @track_call
    def new_follower(self, as_actor: ap.Person, follow: ap.Follow) -> None:
        self.FOLLOWERS[follow.get_object_sync().id].append(
            follow.get_actor_sync().id
        )

    @track_call
    def undo_new_follower(self, as_actor: ap.Person, follow: ap.Follow) -> None:
        self.FOLLOWERS[follow.get_object_sync().id].remove(
            follow.get_actor_sync().id
        )

    @track_call
    def new_following(self, as_actor: ap.Person, follow: ap.Follow) -> None:
        print(f"new following {follow!r}")
        self.FOLLOWING[as_actor.id].append(follow.get_object_sync().id)

    @track_call
    def undo_new_following(
        self, as_actor: ap.Person, follow: ap.Follow
    ) -> None:
        self.FOLLOWING[as_actor.id].remove(follow.get_object_sync().id)

    def followers(self, as_actor: ap.Person) -> List[str]:
        return self.FOLLOWERS[as_actor.id]

    def following(self, as_actor: ap.Person) -> List[str]:
        return self.FOLLOWING[as_actor.id]

    @track_call
    def post_to_remote_inbox(
        self, as_actor: ap.Person, payload_encoded: str, recp: str
    ) -> None:
        payload = json.loads(payload_encoded)
        print(f"post_to_remote_inbox {payload} {recp}")
        act = ap.parse_activity(payload)
        actor = ap.parse_activity(
            self.fetch_iri_sync(recp.replace("/inbox", ""))
        )
        act.process_from_inbox(actor)

    @track_call
    def inbox_like(self, as_actor: ap.Person, activity: ap.Like) -> None:
        pass

    @track_call
    def inbox_undo_like(self, as_actor: ap.Person, activity: ap.Like) -> None:
        pass

    @track_call
    def outbox_like(self, as_actor: ap.Person, activity: ap.Like) -> None:
        pass

    @track_call
    def outbox_undo_like(self, as_actor: ap.Person, activity: ap.Like) -> None:
        pass

    @track_call
    def inbox_announce(
        self, as_actor: ap.Person, activity: ap.Announce
    ) -> None:
        pass

    @track_call
    def inbox_undo_announce(
        self, as_actor: ap.Person, activity: ap.Announce
    ) -> None:
        pass

    @track_call
    def outbox_announce(
        self, as_actor: ap.Person, activity: ap.Announce
    ) -> None:
        pass

    @track_call
    def outbox_undo_announce(
        self, as_actor: ap.Person, activity: ap.Announce
    ) -> None:
        pass

    @track_call
    def inbox_delete(self, as_actor: ap.Person, activity: ap.Delete) -> None:
        pass

    @track_call
    def outbox_delete(self, as_actor: ap.Person, activity: ap.Delete) -> None:
        pass

    @track_call
    def inbox_update(self, as_actor: ap.Person, activity: ap.Update) -> None:
        pass

    @track_call
    def outbox_update(self, as_actor: ap.Person, activity: ap.Update) -> None:
        pass

    @track_call
    def inbox_create(self, as_actor: ap.Person, activity: ap.Create) -> None:
        pass

    @track_call
    def outbox_create(self, as_actor: ap.Person, activity: ap.Create) -> None:
        pass


# Tests for _run_sync helper
def test_run_sync_non_coroutine():
    """Test _run_sync with a non-coroutine value."""
    result = _run_sync(42)
    assert result == 42


def test_run_sync_with_string():
    """Test _run_sync with a string value."""
    result = _run_sync("hello")
    assert result == "hello"


def test_run_sync_with_none():
    """Test _run_sync with None."""
    result = _run_sync(None)
    assert result is None


@pytest.mark.asyncio
async def test_run_sync_from_async_context_raises():
    """Test that _run_sync raises RuntimeError when called from async context."""

    async def dummy_coro():
        return 42

    coro = dummy_coro()
    with pytest.raises(
        RuntimeError, match="Cannot run async code from within an async context"
    ):
        _run_sync(coro)
    # Clean up the coroutine if not consumed
    try:
        await coro
    except RuntimeError:
        pass


def test_run_sync_from_sync_context():
    """Test that _run_sync works from sync context."""

    async def dummy_coro():
        return "success"

    result = _run_sync(dummy_coro())
    assert result == "success"


# Tests for Backend base class
class TestBackendBase:
    """Test Backend base class methods."""

    def test_debug_mode_default(self):
        """Test that debug_mode returns False by default."""

        # Create a minimal concrete Backend subclass
        class TestBackend(Backend):
            def base_url(self) -> str:
                return "https://test.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://test.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://test.com/note/{obj_id}"

        back = TestBackend()
        assert back.debug_mode() is False

    def test_user_agent(self):
        """Test that user_agent returns expected format."""
        back = InMemBackend()
        ua = back.user_agent()
        assert "Active Boxes/" in ua
        assert "github.com/tsileo/little-boxes" in ua

    def test_random_object_id(self):
        """Test that random_object_id returns a hex string."""
        back = InMemBackend()
        obj_id = back.random_object_id()
        assert isinstance(obj_id, str)
        assert len(obj_id) == 16  # 8 bytes = 16 hex chars

    def test_random_object_id_unique(self):
        """Test that random_object_id returns unique values."""
        back = InMemBackend()
        ids = {back.random_object_id() for _ in range(100)}
        assert len(ids) == 100

    def test_extra_inboxes_default(self):
        """Test that extra_inboxes returns empty list by default."""
        back = InMemBackend()
        assert back.extra_inboxes() == []


@pytest.mark.asyncio
class TestBackendAsync:
    """Test Backend async methods."""

    async def test_check_url_async(self):
        """Test async check_url method."""
        back = InMemBackend()
        await back.check_url("https://example.com")  # Should not raise

    async def test_fetch_json_async(self):
        """Test async fetch_json method."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/data"] = {"test": "data"}

        result = await back.fetch_json("https://example.com/data")
        assert result == {"test": "data"}

    async def test_fetch_json_async_with_headers(self):
        """Test async fetch_json with custom headers."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/data"] = {"test": "data"}

        result = await back.fetch_json(
            "https://example.com/data", headers={"Custom": "header"}
        )
        assert result == {"test": "data"}

    async def test_fetch_iri_async(self):
        """Test async fetch_iri method."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/actor"] = {
            "id": "https://example.com/actor",
            "type": "Person",
        }

        result = await back.fetch_iri("https://example.com/actor")
        assert result["id"] == "https://example.com/actor"

    async def test_fetch_iri_async_invalid_iri(self):
        """Test fetch_iri with invalid IRI."""

        # Create a minimal backend that uses base fetch_iri implementation
        class TestBackend(Backend):
            def base_url(self) -> str:
                return "https://test.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://test.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://test.com/note/{obj_id}"

        back = TestBackend()

        # Invalid IRI (not starting with http) should raise NotAnActivityError
        with pytest.raises(ap.NotAnActivityError, match="not a valid IRI"):
            await back.fetch_iri("not-a-valid-iri")

    async def test_fetch_iri_async_error_propagation(self):
        """Test that errors from get_json propagate correctly."""

        # Create a minimal backend that uses base fetch_iri implementation
        class TestBackend(Backend):
            def base_url(self) -> str:
                return "https://test.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://test.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://test.com/note/{obj_id}"

        back = TestBackend()

        # Mock check_url to pass and get_http_client to raise an error
        with mock.patch.object(back, "check_url"):
            with mock.patch(
                "active_boxes.backend.get_http_client"
            ) as mock_client:
                mock_client_instance = mock.AsyncMock()
                mock_client_instance.get_json.side_effect = (
                    ap.ActivityNotFoundError("Not found")
                )
                mock_client.return_value = mock_client_instance

                with pytest.raises(ap.ActivityNotFoundError):
                    await back.fetch_iri("https://example.com/missing")

    async def test_parse_collection_async(self):
        """Test async parse_collection method."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/collection"] = {
            "type": "Collection",
            "items": [1, 2, 3],
        }

        result = await back.parse_collection_async(
            url="https://example.com/collection"
        )
        assert result == [1, 2, 3]


class TestBackendSync:
    """Test Backend sync wrapper methods."""

    def test_check_url_sync(self):
        """Test sync check_url wrapper."""
        back = InMemBackend()
        back.check_url_sync("https://example.com")  # Should not raise

    def test_fetch_json_sync(self):
        """Test sync fetch_json wrapper."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/data"] = {"test": "data"}

        result = back.fetch_json_sync("https://example.com/data")
        assert result == {"test": "data"}

    def test_fetch_iri_sync(self):
        """Test sync fetch_iri wrapper."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/actor"] = {
            "id": "https://example.com/actor",
            "type": "Person",
        }

        result = back.fetch_iri_sync("https://example.com/actor")
        assert result["id"] == "https://example.com/actor"

    def test_parse_collection_sync(self):
        """Test sync parse_collection method."""
        back = InMemBackend()
        back.FETCH_MOCK["https://example.com/collection"] = {
            "type": "Collection",
            "items": [1, 2, 3],
        }

        result = back.parse_collection(url="https://example.com/collection")
        assert result == [1, 2, 3]

    def test_is_from_outbox(self):
        """Test is_from_outbox method."""
        back = InMemBackend()
        ap.use_backend(back)

        # Create a person and activity
        person = back.setup_actor("Test User", "test")
        note = ap.Note(
            content="Test",
            attributedTo=person.id,
            to=[ap.AS_PUBLIC],
        )
        create = note.build_create()
        create.set_id(back.activity_url("test-activity"), "test-activity")

        # Test is_from_outbox
        assert back.is_from_outbox(person, create) is True

        # Test with different actor
        other_person = back.setup_actor("Other User", "other")
        assert back.is_from_outbox(other_person, create) is False


class TestAsyncBackend:
    """Test AsyncBackend class."""

    @pytest.mark.asyncio
    async def test_get_json(self):
        """Test AsyncBackend.get_json calls fetch_json."""

        class ConcreteAsyncBackend(AsyncBackend):
            def base_url(self) -> str:
                return "https://example.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://example.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://example.com/note/{obj_id}"

        back = ConcreteAsyncBackend()
        back.fetch_json = mock.AsyncMock(return_value={"test": "data"})

        result = await back.get_json("https://example.com")
        assert result == {"test": "data"}
        back.fetch_json.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_post_json(self):
        """Test AsyncBackend.post_json method."""

        class ConcreteAsyncBackend(AsyncBackend):
            def base_url(self) -> str:
                return "https://example.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://example.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://example.com/note/{obj_id}"

        back = ConcreteAsyncBackend()

        with mock.patch("active_boxes.backend.get_http_client") as mock_client:
            mock_client_instance = mock.AsyncMock()
            mock_client_instance.post_json = mock.AsyncMock()
            mock_client.return_value = mock_client_instance

            await back.post_json(
                "https://example.com/inbox",
                {"test": "data"},
                headers={"Custom": "header"},
            )

            mock_client_instance.post_json.assert_called_once()
            call_args = mock_client_instance.post_json.call_args
            assert call_args[0][0] == "https://example.com/inbox"
            assert call_args[0][1] == {"test": "data"}

    @pytest.mark.asyncio
    async def test_post_json_with_custom_headers(self):
        """Test AsyncBackend.post_json with custom headers."""

        class ConcreteAsyncBackend(AsyncBackend):
            def base_url(self) -> str:
                return "https://example.com"

            def activity_url(self, obj_id: str) -> str:
                return f"https://example.com/activity/{obj_id}"

            def note_url(self, obj_id: str) -> str:
                return f"https://example.com/note/{obj_id}"

        back = ConcreteAsyncBackend()

        with mock.patch("active_boxes.backend.get_http_client") as mock_client:
            mock_client_instance = mock.AsyncMock()
            mock_response = mock.AsyncMock()
            mock_client_instance.post_json.return_value = mock_response
            mock_client.return_value = mock_client_instance

            await back.post_json(
                "https://example.com/inbox",
                {"test": "data"},
                headers={"X-Custom": "value"},
            )

            # Verify headers were merged
            call_kwargs = mock_client_instance.post_json.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["X-Custom"] == "value"
