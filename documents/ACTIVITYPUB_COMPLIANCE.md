# ActivityPub Protocol Compliance Requirements

## Overview

ActivityPub is a decentralized social networking protocol based on the ActivityStreams 2.0 data format. It provides a client to server API for creating, updating and deleting content, as well as a federated server to server API for delivering notifications and content.

## Core Protocol Requirements

### 1. Server Implementation

#### 1.1. Client to Server Interactions

| Feature | Status | Notes |
|---------|--------|-------|
| Create | [x] Implemented | Wraps non-Activity objects in Create automatically |
| Update | [x] Implemented | Supports CREATE_TYPES and ACTOR_TYPES |
| Delete | [x] Implemented | Handles Tombstone for deleted objects |
| Follow | [x] Implemented | Allowed object: ACTOR_TYPES |
| Undo | [x] Implemented | Supports FOLLOW, LIKE, ANNOUNCE, BLOCK undo |
| Add | [x] Implemented | Requires object AND target |
| Remove | [x] Implemented | Requires object AND target |
| Like | [x] Implemented | Allowed: CREATE_TYPES |
| Block | [x] Implemented | Simple implementation |
| Accept | [x] Implemented | Allowed object: FOLLOW only |
| Reject | [x] Implemented | Allowed object: FOLLOW only |
| Announce | [x] Implemented | Full boost/reshare with recipient tracking |

#### 1.2. Server to Server Interactions

| Feature | Status | Notes |
|---------|--------|-------|
| Delivery | [-] Partial | recipients() computes recipients but no actual POST delivery in backend |
| Inbox | [-] Partial | No POST endpoint, no deduplication |
| Outbox | [-] Partial | GET works, no POST submission |
| Follow handling | [x] Implemented | Backend manages follower relationships |
| HTTP Signatures | [x] Implemented | httpsig.py for signing/verification |
| LD Signatures | [x] Implemented | linked_data_sig.py |

---

## Objects and Activities

### Required Actor Types - [x] All Implemented

- Person [x]
- Application [x]
- Group [x]
- Organization [x]
- Service [x]

### Required Activity Types

#### Core Activities (Sections 6.2-6.11, 7.2-7.12) - [x] All Implemented

| Activity | Status | Notes |
|----------|--------|-------|
| Create | [x] | Object wrapping, is_public() check, attributedTo |
| Update | [x] | Supports CREATE_TYPES and ACTOR_TYPES |
| Delete | [x] | Tombstone handling, _get_actual_object() |
| Follow | [x] | build_undo() helper |
| Accept | [x] | Object: FOLLOW only |
| Reject | [x] | Object: FOLLOW only |
| Add | [x] | Requires object AND target |
| Remove | [x] | Requires object AND target |
| Like | [x] | build_undo() helper |
| Block | [x] | Simple implementation |
| Undo | [x] | FOLLOW, LIKE, ANNOUNCE, BLOCK |
| Announce | [x] | Recipient tracking |

#### Extended Activities - [x] Implemented

| Activity | Status | Notes |
|----------|--------|-------|
| Flag | [x] | Used for reporting/moderation |
| Move | [x] | Actor migration |
| Join | [x] | Joining groups |
| Leave | [x] | Leaving groups |
| View | [x] | User viewing content |
| Listen | [x] | User listening to audio |
| Read | [x] | User reading articles |
| Write | [x] | Writing to collection |
| Travel | [x] | User traveling |
| Arrive | [x] | User arriving at location |

### Required Object Types - [x] All Implemented

| Type | Status |
|------|--------|
| Note | [x] |
| Article | [x] |
| Image | [x] |
| Video | [x] |
| Audio | [x] |
| Document | [x] |
| Page | [x] |
| Event | [x] |
| Place | [x] |
| Profile | [x] |
| Relationship | [x] |
| Tombstone | [x] |
| Question | [x] |
| Mention | [x] |
| Hashtag | [x] (via context) |

### Actor Properties

#### Required - [x] All Implemented

| Property | Status |
|----------|--------|
| inbox | [x] |
| outbox | [x] |

#### Recommended - [x] All Implemented

| Property | Status |
|----------|--------|
| following | [x] |
| followers | [x] |
| liked | [-] Partial - not explicit on actors |

#### Optional/Mastodon Extension - [x] All Implemented

| Property | Status | Notes |
|----------|--------|-------|
| preferredUsername | [x] |
| endpoints | [-] | Only sharedInbox handled |
| sharedInbox | [x] |
| streams | [x] | `get_streams()`, `add_stream()` |
| manuallyApprovesFollowers | [x] | `manually_approves_followers()`, `requires_follow_approval()` |
| publicKey | [x] | Delegated to key.py |

---

## Collections

### Collection Classes - [x] Implemented

| Collection | Status |
|------------|--------|
| Collection | [x] |
| OrderedCollection | [x] |
| CollectionPage | [x] |
| OrderedCollectionPage | [x] |

### Collection Pagination - [x] Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| first link | [x] | Followed automatically |
| next link | [x] | Forward pagination |
| prev link | [x] | Backward pagination via `iterate_backward()` |
| last link | [x] | Supported in `iterate_backward()` |
| partOf | [x] | Validated via `validate_part_of()` |
| totalItems | [x] | Tracked in CollectionPage |
| Recursion limit | [x] | Configurable via `max_depth` |

### Special Collections

| Collection | Status | Notes |
|------------|--------|-------|
| Outbox | [x] | OrderedCollection |
| Inbox | [x] | OrderedCollection |
| Followers | [x] | Collection or OrderedCollection |
| Following | [x] | Collection or OrderedCollection |
| Liked | [ ] | Not explicitly on actors |
| Likes (per-object) | [x] | Implemented via `build_likes_collection()` |
| Shares (per-object) | [x] | Implemented via `build_shares_collection()` |
| Featured | [x] | Implemented via `build_featured_collection()` |
| Replies | [x] | Implemented via `build_replies_collection()` |

---

## HTTP Signatures - [x] Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Signature Generation | [x] | HTTPSigAuth class |
| Signature Verification | [x] | verify_request() |
| Digest Header | [x] | RFC 7231 compliant |
| Date Header | [x] | Replay attack prevention |
| Key Retrieval | [x] | Via actor publicKey |

---

## AsyncIO Support - [x] Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Async Backend | [x] | `Backend` with async methods (`fetch_json()`, `fetch_iri()`) |
| AsyncHTTPClient | [x] | `http_client.py` with aiohttp |
| Async WebFinger | [x] | `webfinger()` (async-primary), `webfinger_sync()` wrapper |
| Async HTTPSignatures | [x] | `verify_request()`, `sign_request()` (async-primary) |
| Async Collection Parsing | [x] | `parse_collection()`, `CollectionPaginator` |
| Sync Wrappers | [x] | `_sync()` suffix for Flask/Django compatibility |

### Async-First API Design

The library uses an **async-first** naming convention where the primary method names are async:

```python
# Async (recommended for new code)
actor = await fetch_iri(actor_url)
data = await fetch_json(url)
activity = await get_object()

# Sync wrappers (for Flask/Django)
actor = fetch_iri_sync(actor_url)
data = fetch_json_sync(url)
activity = get_object_sync()
```

This design enables:
- Clean async code for FastAPI, aiohttp, Quart, etc.
- Backwards compatibility with Flask, Django sync views via `_sync()` wrappers
- Clear distinction between async and sync usage patterns

---

## JSON-LD and Context - [x] Implemented

| Feature | Status |
|---------|--------|
| @context inclusion | [x] |
| Security context | [x] |
| Extension context | [x] |
| JSON-LD serialization | [x] |
| ActivityStreams 2.0 | [x] |
| Content negotiation | [x] | `get_accept_header()`, `get_content_type_header()` support activity, ld+json, json, html |

---

## WebFinger - [x] Implemented

| Feature | Status |
|---------|--------|
| WebFinger endpoint | [x] |
| Actor discovery | [x] |
| Proper response format | [x] |
| XRD/JRD format | [x] |

---

## Security Requirements

| Feature | Status | Notes |
|---------|--------|-------|
| HTTP Signature auth | [x] | |
| LD Signature | [x] | |
| Input validation | [x] | |
| Output sanitization | [x] | Via bleach |
| Content security | [x] | `build_csp_header()`, `build_activity_headers()` |
| Origin verification | [ ] | Not explicit |
| Replay prevention | [x] | `verify_date_header()` for Date header freshness |
| bto/bcc handling | [ ] | Not stripped from activities |

---

## Backend Requirements

### Implemented by Library

| Method | Status |
|--------|--------|
| base_url() | [x] (abstract - app implements) |
| activity_url() | [x] (abstract - app implements) |
| note_url() | [x] (abstract - app implements) |
| fetch_iri() / fetch_iri_sync() | [x] GET with redirects (async-primary) |
| fetch_json() / fetch_json_sync() | [x] GET with JSON (async-primary) |
| check_url() / check_url_sync() | [x] |
| user_agent() | [x] |
| random_object_id() | [x] |
| extra_inboxes() | [x] (hook for app to add recipients) |
| is_from_outbox() | [x] |
| parse_collection() / parse_collection_sync() | [x] |
| get_first_page() | [x] CollectionPaginator |
| iterate_forward() | [x] CollectionPaginator |
| iterate_backward() | [x] CollectionPaginator |

### App Must Implement (via `ActivityPubPlugin` Protocol)

| Feature | Protocol Method | Notes |
|---------|-----------------|-------|
| post_to_inbox/deliver() | `deliver_activity()` | Sign & POST to remote inboxes |
| inbox deduplication | `is_duplicate()` | Track seen activity IDs |
| activity storage | `store_activity()`/`get_activity()` | Persist activities |
| actor caching | `store_actor()`/`get_actor()` | Cache fetched actors |
| inbox processing | `receive_activity()` | Process incoming activities |
| retry/backoff | App logic | Queue/retry policy is app's job |
| batch delivery | App logic | App can batch if needed |
| delivery queue | App logic | App manages delivery queue |

---

## Missing Features Requiring Implementation

> **Note:** This library defines a `plugin.Protocol` (see `active_boxes/plugin.py`) that specifies what applications MUST implement vs what the library provides. Many "missing" features below are correctly omitted because they're the application's responsibility.

### High Priority (Library Gaps - Should Implement)

1. [x] **Extended Activities** - Flag, Move, Join, Leave, View, Listen, Read, Write, Travel, Arrive Implemented
2. [x] **Per-object Likes/Shares collections** - Library helpers for `Likes` and `Shares` collections
3. [x] **Featured Collection** - For profile pages (`toot:featured`)
4. [x] **Backward Pagination** - `prev` link support via `iterate_backward()`
5. [x] **streams Property** - `get_streams()`, `add_stream()` on Person
6. [x] **manuallyApprovesFollowers** - `manually_approves_followers()`, `requires_follow_approval()` on Person
7. [x] **Replies Collection** - `build_replies_collection()` helper
8. [x] **Content Security Policy** - `build_csp_header()`, `build_activity_headers()`
9. [x] **Replay Attack Prevention** - `verify_date_header()` for Date header freshness
10. [x] **AsyncIO Support** - Full async implementation with aiohttp

### High Priority (App Responsibility - See `DeliveryPlugin` Protocol)

The following are **NOT library gaps** - they require app implementation via the `ActivityPubPlugin` protocol:

1. **`deliver_activity()`** - App signs and POSTs to remote inboxes
2. **`receive_activity()`** - App processes incoming activities
3. **`is_duplicate()`** - App tracks seen activity IDs
4. **`store_activity()`/`get_activity()`** - App persists activities

The library handles:

- Computing recipients via `recipients()` method
- Activity serialization/deserialization
- HTTP Signature generation (via `httpsig.py`)
- HTTP Signature verification (via `httpsig.py`)

### Medium Priority

1. **Retry Logic** - App responsibility (queue/retry policy)
2. **bto/bcc Handling** - Library strips from output, app should respect
3. **Origin Verification** - App responsibility (via `verify_origin()` hook)

### Low Priority / Nice to Have

1. [x] **Extended Activities** - All implemented
2. [x] **per-object Likes/Shares** - Activity collections on objects
3. [x] **Replies Collection** - Threaded conversations
4. [x] **Replay Attack Prevention** - Verify Date header freshness
5. [ ] **Origin Verification** - Verify activity origin
6. [x] **Content Security Policy** - Explicit CSP headers

---

## Compliance Checklist

### Library vs App Responsibilities

| Requirement | Status | Responsibility |
|-------------|--------|----------------|
| Client to Server API | [x] | Library + App |
| Server to Server API | [-] Partial | Library computes, App delivers |
| Inbox processing | [-] Partial | App implements via `InboxPlugin` |
| Outbox processing | [-] Partial | App implements via `CollectionPlugin` |
| WebFinger support | [x] | Library |
| HTTP Signatures | [x] | Library (`httpsig.py`) |
| LD Signatures | [x] | Library (`linked_data_sig.py`) |
| JSON-LD support | [x] | Library |

### Object Requirements

| Requirement | Status |
|-------------|--------|
| Actor types | [x] All |
| Activity types (core) | [x] All |
| Activity types (extended) | [x] All |
| Object types | [x] All |
| Properties validation | [x] |
| Collection support | [-] Partial |

### Security Requirements

| Requirement | Status |
|-------------|--------|
| HTTP Signature generation | [x] |
| HTTP Signature verification | [x] |
| LD Signature | [x] |
| Input validation | [x] |
| Output sanitization | [x] |
| Authentication | [x] |
| Authorization | [-] Partial |
| bto/bcc handling | [ ] |

### Federation Requirements

| Requirement | Status | Responsibility |
|-------------|--------|----------------|
| Actor discovery | [x] | Library (via `fetch_iri`) |
| Content distribution | [-] Partial | App implements `deliver_activity()` |
| Follower management | [x] | Library + App |
| Block handling | [x] | Library |
| Error handling | [x] | Library |
| Deduplication | [ ] | App via `is_duplicate()` |

---

## References

1. [ActivityPub Specification](https://www.w3.org/TR/activitypub/)
2. [ActivityStreams 2.0](https://www.w3.org/TR/activitystreams-core/)
3. [JSON-LD 1.0](https://www.w3.org/TR/json-ld/)
4. [HTTP Signatures Draft](https://tools.ietf.org/html/draft-cavage-http-signatures-12)
5. [WebFinger RFC](https://tools.ietf.org/html/rfc7033)
