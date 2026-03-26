"""ActivityPub plugin interface for application backends.

This module defines the Protocol that any application backend must implement
to use the active_boxes library for ActivityPub federation.

This is an **async library** - all network I/O methods use asyncio.
Your app should use asyncio, FastAPI, aiohttp, or any async framework.

Example usage with asyncio:
    from active_boxes.plugin import ActivityPubPlugin

    class MyAppBackend(ActivityPubPlugin):
        def base_url(self) -> str:
            return "https://myapp.example"

        def activity_url(self, obj_id: str) -> str:
            return f"{self.base_url()}/activity/{obj_id}"

        def note_url(self, obj_id: str) -> str:
            return f"{self.base_url()}/note/{obj_id}"

        async def deliver_activity(
            self,
            activity: dict,
            inbox: str,
            actor: dict,
        ) -> bool:
            signed = sign_request(activity, actor)
            async with httpx.AsyncClient() as client:
                resp = await client.post(inbox, json=signed)
            return resp.status_code in (200, 201, 202)

        async def receive_activity(
            self,
            activity: dict,
            source_inbox: str | None = None,
        ) -> bool:
            if self.is_duplicate(activity["id"]):
                return False
            await self.store_activity(activity, source_inbox)
            await self.process_activity(activity)
            return True

        def is_duplicate(self, activity_id: str) -> bool:
            return False  # No deduplication by default
"""

from typing import List, Protocol, runtime_checkable

from .activitypub import ObjectType


@runtime_checkable
class DeliveryPlugin(Protocol):
    """Protocol for ActivityPub delivery - the app handles actual HTTP POST.

    The library computes recipients and prepares the activity, but the app
    is responsible for signing and delivering to remote inboxes.
    """

    async def deliver_activity(
        self,
        activity: ObjectType,
        inbox: str,
        actor: ObjectType,
    ) -> bool:
        """Deliver an activity to a remote inbox.

        Args:
            activity: The ActivityPub activity dict to deliver
            inbox: The target inbox URL
            actor: The sender actor dict (must have privateKey for signing)

        Returns:
            True if delivery succeeded (2xx status), False otherwise

        Raises:
            Any exception will be caught and logged by the library
        """
        ...


@runtime_checkable
class InboxPlugin(Protocol):
    """Protocol for receiving activities from remote servers."""

    async def receive_activity(
        self,
        activity: ObjectType,
        source_inbox: str | None = None,
    ) -> bool:
        """Process an activity received from a remote inbox.

        Args:
            activity: The ActivityPub activity dict received
            source_inbox: The inbox URL it came from (for deduplication)

        Returns:
            True if processed successfully, False if skipped/deduplicated

        Raises:
            Any exception will be caught and logged by the library
        """
        ...

    def is_duplicate(self, activity_id: str) -> bool:
        """Check if an activity was already processed.

        Args:
            activity_id: The activity's id field

        Returns:
            True if already seen (skip processing), False to process
        """
        ...


@runtime_checkable
class StoragePlugin(Protocol):
    """Protocol for persisting activities and objects."""

    def store_activity(
        self,
        activity: ObjectType,
        recipient_inbox: str | None = None,
    ) -> None:
        """Persist an activity to storage.

        Args:
            activity: The activity dict to store
            recipient_inbox: If received via inbox, which one
        """
        ...

    def get_activity(self, activity_id: str) -> ObjectType | None:
        """Retrieve a stored activity by ID."""
        ...

    def store_actor(self, actor: ObjectType) -> None:
        """Cache an actor locally."""
        ...

    def get_actor(self, actor_id: str) -> ObjectType | None:
        """Retrieve a cached actor by ID."""
        ...


@runtime_checkable
class CollectionPlugin(Protocol):
    """Protocol for building ActivityPub collections."""

    def get_outbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> ObjectType:
        """Build an outbox OrderedCollection for an actor.

        Args:
            actor_id: The actor's ID
            page: Page number for pagination (None for first page)

        Returns:
            OrderedCollection or OrderedCollectionPage dict
        """
        ...

    def get_inbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> ObjectType:
        """Build an inbox OrderedCollection for an actor."""
        ...

    def get_followers(self, actor_id: str) -> ObjectType:
        """Build a followers Collection for an actor."""
        ...

    def get_following(self, actor_id: str) -> ObjectType:
        """Build a following Collection for an actor."""
        ...

    def get_liked(self, actor_id: str) -> ObjectType:
        """Build a liked Collection for an actor."""
        ...


@runtime_checkable
class ActivityPubPlugin(
    DeliveryPlugin,
    InboxPlugin,
    StoragePlugin,
    CollectionPlugin,
    Protocol,
):
    """Full ActivityPub plugin protocol.

    This is an **async** protocol - network I/O methods use asyncio.

    A class implementing this protocol can be passed to use_backend()
    and provides everything needed for ActivityPub federation.

    The app MUST implement:
        - base_url() - The application's base URL
        - activity_url() - URL for activity objects
        - note_url() - URL for note objects
        - deliver_activity() - Async: POST to remote inboxes
        - receive_activity() - Async: Process incoming activities
        - is_duplicate() - Deduplication check

    The app SHOULD implement:
        - extra_inboxes() - Add extra recipients for all activities
        - store_activity() / get_activity() - Persist activities
        - store_actor() / get_actor() - Cache actors
        - get_outbox() / get_inbox() / get_followers() / get_following() / get_liked()
    """

    # === Required: URL generation ===

    def base_url(self) -> str:
        """Return the application's base URL (e.g., 'https://example.com')."""
        ...

    def activity_url(self, obj_id: str) -> str:
        """Return the URL for an activity with the given object ID."""
        ...

    def note_url(self, obj_id: str) -> str:
        """Return the URL for a note with the given object ID."""
        ...

    # === Required: Delivery (outbound) ===

    async def deliver_activity(
        self,
        activity: ObjectType,
        inbox: str,
        actor: ObjectType,
    ) -> bool:
        """Sign and deliver an activity to a remote inbox."""
        ...

    # === Required: Inbox (inbound) ===

    async def receive_activity(
        self,
        activity: ObjectType,
        source_inbox: str | None = None,
    ) -> bool:
        """Process an activity received from a remote inbox."""
        ...

    def is_duplicate(self, activity_id: str) -> bool:
        """Check if an activity was already processed."""
        ...

    # === Optional: Extra recipients ===

    def extra_inboxes(self) -> List[str]:
        """Return additional inbox URLs for every outgoing activity.

        This is called by the library when computing recipients for
        Create activities. Use this for shared inbox endpoints or
        other delivery targets that should receive all activities.

        Default: return empty list
        """
        return []

    # === Optional: Storage ===

    def store_activity(
        self,
        activity: ObjectType,
        recipient_inbox: str | None = None,
    ) -> None:
        """Persist an activity to storage.

        Default: no-op
        """
        ...

    def get_activity(self, activity_id: str) -> ObjectType | None:
        """Retrieve a stored activity by ID.

        Default: return None
        """
        return None

    def store_actor(self, actor: ObjectType) -> None:
        """Cache an actor locally.

        Default: no-op
        """
        ...

    def get_actor(self, actor_id: str) -> ObjectType | None:
        """Retrieve a cached actor by ID.

        Default: return None (library will fetch from network)
        """
        return None

    # === Optional: Collections ===

    def get_outbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> ObjectType:
        """Build an outbox OrderedCollection for an actor.

        Default: raises NotImplementedError
        """
        raise NotImplementedError

    def get_inbox(
        self,
        actor_id: str,
        page: int | None = None,
    ) -> ObjectType:
        """Build an inbox OrderedCollection for an actor.

        Default: raises NotImplementedError
        """
        raise NotImplementedError

    def get_followers(self, actor_id: str) -> ObjectType:
        """Build a followers Collection for an actor.

        Default: raises NotImplementedError
        """
        raise NotImplementedError

    def get_following(self, actor_id: str) -> ObjectType:
        """Build a following Collection for an actor.

        Default: raises NotImplementedError
        """
        raise NotImplementedError

    def get_liked(self, actor_id: str) -> ObjectType:
        """Build a liked Collection for an actor.

        Default: raises NotImplementedError
        """
        raise NotImplementedError

    # === Optional: Identity verification ===

    def verify_origin(self, activity: ObjectType, actor: ObjectType) -> bool:
        """Verify that an activity originated from the claimed actor.

        This checks HTTP signatures, LD signatures, or other proofs.

        Default: return True (trust the library's signature verification)
        """
        return True
