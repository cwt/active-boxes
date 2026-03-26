# Active Boxes (Modernized Little Boxes)

This project is a fork of [Little Boxes](https://github.com/tsileo/little-boxes) that has been modernized and relicensed from ISC to MIT.

**Modernization Complete, ActivityPub Compliance In Progress**

This project has been successfully modernized and updated to current Python packaging standards and Python 3.10+ features. Core ActivityPub functionality is implemented, with federation delivery features under development.

The original README can be found in [ORIGINAL-README.md](ORIGINAL-README.md).

## Current Status

- [x] Migrated from `setup.py` to `pyproject.toml`
- [x] Moved development dependencies to `pyproject.toml`
- [x] Switched to Poetry for dependency management and building
- [x] Updated to require Python 3.10+
- [x] Created comprehensive modernization plans
- [x] Modernized codebase to leverage Python 3.10+ features
- [x] Created comprehensive test suite
- [x] ActivityPub protocol compliance - Core 11 activities, Extended activities
- [x] Updated documentation and examples
- [x] Prepared for stable release

## Modernization Features

### Python 3.10+ Features

- Structural Pattern Matching (match/case statements)
- Modern Union Types (`X | Y` syntax instead of `Union[X, Y]`)
- Parenthesized context managers
- Improved type hinting throughout the codebase
- Walrus operator usage where appropriate
- Modern string formatting with f-strings

### Code Quality

- 100% type hinting coverage
- Comprehensive test suite with ~89% code coverage
- Modern code formatting with Black
- Strict linting with Ruff
- Type checking with MyPy

### Testing

- ActivityPub protocol compliance testing (core + extended activities)
- Integration tests with mock servers
- Property-based testing for robustness
- Security-focused test suite (~89% coverage)

## Implemented ActivityPub Features

### Core Activities [x]

Create, Update, Delete, Follow, Accept, Reject, Add, Remove, Like, Block, Undo, Announce

### Extended Activities [x]

Flag, Move, Join, Leave, View, Listen, Read, Write, Travel, Arrive

### Actor Properties [x]

inbox, outbox, following, followers, preferredUsername, endpoints (sharedInbox)

### Collections [x]

Collection, OrderedCollection, CollectionPage, OrderedCollectionPage

### Security [x]

HTTP Signatures (generation/verification), Linked Data Signatures

### Plugin Interface [x]

`active_boxes.plugin.ActivityPubPlugin` - Protocol defining app responsibilities

### Missing (Under Development)

- Per-object Likes/Shares collections
- Backward pagination in collections
- Featured collection support

## Quick Start

**This is an async library** - your plugin should use `asyncio` or any async framework (FastAPI, aiohttp, etc.).

### 1. Implement the Plugin Protocol

```python
from active_boxes import activitypub as ap
from active_boxes.plugin import ActivityPubPlugin

class MyAppPlugin(ActivityPubPlugin):
    BASE_URL = "https://myapp.example"

    # Required: URL generation
    def base_url(self) -> str:
        return self.BASE_URL

    def activity_url(self, obj_id: str) -> str:
        return f"{self.BASE_URL}/activity/{obj_id}"

    def note_url(self, obj_id: str) -> str:
        return f"{self.BASE_URL}/note/{obj_id}"

    # Required: Deliver activities to remote inboxes
    async def deliver_activity(
        self,
        activity: dict,
        inbox: str,
        actor: dict,
    ) -> bool:
        signed = self.sign_request(activity, actor)
        async with httpx.AsyncClient() as client:
            resp = await client.post(inbox, json=signed)
        return resp.status_code in (200, 201, 202)

    # Required: Process incoming activities
    async def receive_activity(
        self,
        activity: dict,
        source_inbox: str | None = None,
    ) -> bool:
        if self.is_duplicate(activity["id"]):
            return False  # Skip duplicate
        await self.store_activity(activity, source_inbox)
        await self.process_activity(activity)
        return True

    # Required: Deduplication
    def is_duplicate(self, activity_id: str) -> bool:
        return self.redis.exists(f"activity:{activity_id}")

    # Optional: Add extra recipients for all activities
    def extra_inboxes(self) -> list[str]:
        return []  # Or add a shared inbox

    def sign_request(self, activity: dict, actor: dict) -> dict:
        # Your HTTP signature logic here
        ...
```

### 2. Initialize the Backend

```python
from active_boxes import activitypub as ap

plugin = MyAppPlugin()
ap.use_backend(plugin)
```

### 3. Create and Send Activities

```python
# Create a note
note = ap.Note(
    content="Hello, federation!",
    attributedTo="https://myapp.example/user/alice",
    to=[ap.AS_PUBLIC],
)

# Create the activity wrapping the note
create = note.build_create()
create.set_id("https://myapp.example/activity/abc123", "abc123")

# Get recipients and deliver
recipients = create.recipients()  # Computed by library
for inbox in recipients:
    actor = fetch_actor(create.get_actor().id)
    await plugin.deliver_activity(create.to_dict(), inbox, actor)
```

### 4. Receive Activities

```python
# In your inbox endpoint handler
async def inbox_handler(request):
    activity = await request.json()
    await plugin.receive_activity(activity, source_inbox=str(request.url))
    return web.Response(status=202)
```

### 5. Working with Actors

```python
# Create a person actor
person = ap.Person(
    id="https://myapp.example/user/alice",
    inbox="https://myapp.example/user/alice/inbox",
    outbox="https://myapp.example/user/alice/outbox",
    followers="https://myapp.example/user/alice/followers",
    preferredUsername="alice",
    publicKey={
        "id": "https://myapp.example/user/alice#main-key",
        "owner": "https://myapp.example/user/alice",
        "publicKeyPem": "-----BEGIN PUBLIC KEY-----...",
    },
)
```

### 6. Collection Pagination

```python
# Build a paginated outbox
outbox = ap.OrderedCollection(
    id="https://myapp.example/user/alice/outbox",
    totalItems=42,
    first="https://myapp.example/user/alice/outbox?page=1",
)

# Library handles parsing remote collections
items = backend.parse_collection(url="https://example.com/user/bob/outbox")
```

## Plugin Responsibilities

| What Library Does | What Your App Does |
|-------------------|-------------------|
| Activity/Object serialization | HTTP client setup (httpx, aiohttp, etc.) |
| Computing recipients | Signing outgoing requests (HTTP Signatures) |
| HTTP Signature generation | Delivering to remote inboxes |
| HTTP Signature verification | Receiving from remote inboxes |
| Collection pagination | Storing activities persistently |
| Activity vocabulary (Create, Follow, etc.) | Deduplication |
| WebFinger support | Retry/backoff logic |

## Modernization Plans

Detailed planning documents have been created to guide the modernization effort:

- [MODERNIZE_PLAN.md](documents/MODERNIZE_PLAN.md) - Overall modernization strategy
- [PYTHON_310_MODERNIZATION.md](documents/PYTHON_310_MODERNIZATION.md) - Python 3.10+ feature implementation
- [TEST_SUITE_IMPROVEMENTS.md](documents/TEST_SUITE_IMPROVEMENTS.md) - Test suite enhancement plans
- [ACTIVITYPUB_COMPLIANCE.md](documents/ACTIVITYPUB_COMPLIANCE.md) - ActivityPub protocol compliance requirements
- [IMPLEMENTATION_PLAN.md](documents/IMPLEMENTATION_PLAN.md) - Detailed 8-week implementation timeline

## Original Project

For information about the original project, please refer to [ORIGINAL-README.md](ORIGINAL-README.md).
