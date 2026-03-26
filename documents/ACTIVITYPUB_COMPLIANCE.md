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

#### Optional/Mastodon Extension - [-] Partial

| Property | Status | Notes |
|----------|--------|-------|
| preferredUsername | [x] |
| endpoints | [-] | Only sharedInbox handled |
| sharedInbox | [x] |
| streams | [ ] |
| manuallyApprovesFollowers | [-] | In context but not validated |
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

### Collection Pagination - [-] Partial

| Feature | Status | Notes |
|---------|--------|-------|
| first link | [x] | Followed automatically |
| next link | [x] | Forward pagination |
| prev link | [ ] | No backward pagination |
| last link | [ ] | Not implemented |
| partOf | [ ] | No validation |
| totalItems | [ ] | Not tracked |
| Recursion limit | [-] | Limited to 3 levels |

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
| Featured | [-] | In context but no class |
| Replies | [ ] | Not implemented |

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

## JSON-LD and Context - [x] Implemented

| Feature | Status |
|---------|--------|
| @context inclusion | [x] |
| Security context | [x] |
| Extension context | [x] |
| JSON-LD serialization | [x] |
| ActivityStreams 2.0 | [x] |
| Content negotiation | [-] | application/activity+json only, no application/ld+json |

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
| Content security | [-] | Not explicit CSP headers |
| Origin verification | [ ] | Not explicit |
| Replay prevention | [-] | Date header exists but not verified |
| bto/bcc handling | [ ] | Not stripped from activities |

---

## Backend Requirements

### Implemented by Library

| Method | Status |
|--------|--------|
| base_url() | [x] (abstract - app implements) |
| activity_url() | [x] (abstract - app implements) |
| note_url() | [x] (abstract - app implements) |
| fetch_iri() | [x] GET with redirects |
| fetch_json() | [x] GET with JSON |
| check_url() | [x] |
| user_agent() | [x] |
| random_object_id() | [x] |
| extra_inboxes() | [x] (hook for app to add recipients) |
| is_from_outbox() | [x] |
| parse_collection() | [x] |

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
3. [ ] **Featured Collection** - For profile pages (`toot:featured`)
4. [ ] **Backward Pagination** - `prev` link support in collection pagination

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
3. **Replay Attack Prevention** - App responsibility (verify Date header freshness)
4. **Origin Verification** - App responsibility (via `verify_origin()` hook)

### Medium Priority

1. **Retry Logic** - Exponential backoff for failed deliveries
2. **Backward Pagination** - Support prev link in collections
3. **bto/bcc Handling** - Strip before delivery per spec
4. **streams Property** - Supplementary collections
5. **Featured Collection** - For profile pages

### Low Priority / Nice to Have

1. [x] **Extended Activities** - All implemented
2. [x] **per-object Likes/Shares** - Activity collections on objects
3. [ ] **Replies Collection** - Threaded conversations
4. [ ] **Replay Attack Prevention** - Verify Date header freshness
5. [ ] **Origin Verification** - Verify activity origin
6. [ ] **Content Security Policy** - Explicit CSP headers

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
