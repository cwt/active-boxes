# ActivityPub Protocol Compliance Requirements

## Overview

ActivityPub is a decentralized social networking protocol based on the ActivityStreams 2.0 data format. It provides a client to server API for creating, updating and deleting content, as well as a federated server to server API for delivering notifications and content.

## Core Protocol Requirements

### 1. Server Implementation

#### 1.1. Client to Server Interactions

| Feature | Status | Notes |
|---------|--------|-------|
| Create | ✅ Implemented | Wraps non-Activity objects in Create automatically |
| Update | ✅ Implemented | Supports CREATE_TYPES and ACTOR_TYPES |
| Delete | ✅ Implemented | Handles Tombstone for deleted objects |
| Follow | ✅ Implemented | Allowed object: ACTOR_TYPES |
| Undo | ✅ Implemented | Supports FOLLOW, LIKE, ANNOUNCE, BLOCK undo |
| Add | ✅ Implemented | Requires object AND target |
| Remove | ✅ Implemented | Requires object AND target |
| Like | ✅ Implemented | Allowed: CREATE_TYPES |
| Block | ✅ Implemented | Simple implementation |
| Accept | ✅ Implemented | Allowed object: FOLLOW only |
| Reject | ✅ Implemented | Allowed object: FOLLOW only |
| Announce | ✅ Implemented | Full boost/reshare with recipient tracking |

#### 1.2. Server to Server Interactions

| Feature | Status | Notes |
|---------|--------|-------|
| Delivery | ⚠️ Partial | recipients() computes recipients but no actual POST delivery in backend |
| Inbox | ⚠️ Partial | No POST endpoint, no deduplication |
| Outbox | ⚠️ Partial | GET works, no POST submission |
| Follow handling | ✅ Implemented | Backend manages follower relationships |
| HTTP Signatures | ✅ Implemented | httpsig.py for signing/verification |
| LD Signatures | ✅ Implemented | linked_data_sig.py |

---

## Objects and Activities

### Required Actor Types - ✅ All Implemented

- Person ✅
- Application ✅
- Group ✅
- Organization ✅
- Service ✅

### Required Activity Types

#### Core Activities (Sections 6.2-6.11, 7.2-7.12) - ✅ All Implemented

| Activity | Status | Notes |
|----------|--------|-------|
| Create | ✅ | Object wrapping, is_public() check, attributedTo |
| Update | ✅ | Supports CREATE_TYPES and ACTOR_TYPES |
| Delete | ✅ | Tombstone handling, _get_actual_object() |
| Follow | ✅ | build_undo() helper |
| Accept | ✅ | Object: FOLLOW only |
| Reject | ✅ | Object: FOLLOW only |
| Add | ✅ | Requires object AND target |
| Remove | ✅ | Requires object AND target |
| Like | ✅ | build_undo() helper |
| Block | ✅ | Simple implementation |
| Undo | ✅ | FOLLOW, LIKE, ANNOUNCE, BLOCK |
| Announce | ✅ | Recipient tracking |

#### Extended Activities - ❌ Not Implemented

| Activity | Status | Notes |
|----------|--------|-------|
| Flag | ❌ | Used for reporting/moderation |
| Move | ❌ | Actor migration |
| Join | ❌ | Joining groups |
| Leave | ❌ | Leaving groups |
| View | ❌ | User viewing content |
| Listen | ❌ | User listening to audio |
| Read | ❌ | User reading articles |
| Write | ❌ | Writing to collection |
| Travel | ❌ | User traveling |
| Arrive | ❌ | User arriving at location |

### Required Object Types - ✅ All Implemented

| Type | Status |
|------|--------|
| Note | ✅ |
| Article | ✅ |
| Image | ✅ |
| Video | ✅ |
| Audio | ✅ |
| Document | ✅ |
| Page | ✅ |
| Event | ✅ |
| Place | ✅ |
| Profile | ✅ |
| Relationship | ✅ |
| Tombstone | ✅ |
| Question | ✅ |
| Mention | ✅ |
| Hashtag | ✅ (via context) |

### Actor Properties

#### Required - ✅ All Implemented

| Property | Status |
|----------|--------|
| inbox | ✅ |
| outbox | ✅ |

#### Recommended - ✅ All Implemented

| Property | Status |
|----------|--------|
| following | ✅ |
| followers | ✅ |
| liked | ⚠️ Partial - not explicit on actors |

#### Optional/Mastodon Extension - ⚠️ Partial

| Property | Status | Notes |
|----------|--------|-------|
| preferredUsername | ✅ |
| endpoints | ⚠️ | Only sharedInbox handled |
| sharedInbox | ✅ |
| streams | ❌ |
| manuallyApprovesFollowers | ⚠️ | In context but not validated |
| publicKey | ✅ | Delegated to key.py |

---

## Collections

### Collection Classes - ✅ Implemented

| Collection | Status |
|------------|--------|
| Collection | ✅ |
| OrderedCollection | ✅ |
| CollectionPage | ✅ |
| OrderedCollectionPage | ✅ |

### Collection Pagination - ⚠️ Partial

| Feature | Status | Notes |
|---------|--------|-------|
| first link | ✅ | Followed automatically |
| next link | ✅ | Forward pagination |
| prev link | ❌ | No backward pagination |
| last link | ❌ | Not implemented |
| partOf | ❌ | No validation |
| totalItems | ❌ | Not tracked |
| Recursion limit | ⚠️ | Limited to 3 levels |

### Special Collections

| Collection | Status | Notes |
|------------|--------|-------|
| Outbox | ✅ | OrderedCollection |
| Inbox | ✅ | OrderedCollection |
| Followers | ✅ | Collection or OrderedCollection |
| Following | ✅ | Collection or OrderedCollection |
| Liked | ❌ | Not explicitly on actors |
| Likes (per-object) | ❌ | Not implemented |
| Shares (per-object) | ❌ | Not implemented |
| Featured | ⚠️ | In context but no class |
| Replies | ❌ | Not implemented |

---

## HTTP Signatures - ✅ Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Signature Generation | ✅ | HTTPSigAuth class |
| Signature Verification | ✅ | verify_request() |
| Digest Header | ✅ | RFC 7231 compliant |
| Date Header | ✅ | Replay attack prevention |
| Key Retrieval | ✅ | Via actor publicKey |

---

## JSON-LD and Context - ✅ Implemented

| Feature | Status |
|---------|--------|
| @context inclusion | ✅ |
| Security context | ✅ |
| Extension context | ✅ |
| JSON-LD serialization | ✅ |
| ActivityStreams 2.0 | ✅ |
| Content negotiation | ⚠️ | application/activity+json only, no application/ld+json |

---

## WebFinger - ✅ Implemented

| Feature | Status |
|---------|--------|
| WebFinger endpoint | ✅ |
| Actor discovery | ✅ |
| Proper response format | ✅ |
| XRD/JRD format | ✅ |

---

## Security Requirements

| Feature | Status | Notes |
|---------|--------|-------|
| HTTP Signature auth | ✅ | |
| LD Signature | ✅ | |
| Input validation | ✅ | |
| Output sanitization | ✅ | Via bleach |
| Content security | ⚠️ | Not explicit CSP headers |
| Origin verification | ❌ | Not explicit |
| Replay prevention | ⚠️ | Date header exists but not verified |
| bto/bcc handling | ❌ | Not stripped from activities |

---

## Backend Requirements

### Implemented by Library

| Method | Status |
|--------|--------|
| base_url() | ✅ (abstract - app implements) |
| activity_url() | ✅ (abstract - app implements) |
| note_url() | ✅ (abstract - app implements) |
| fetch_iri() | ✅ GET with redirects |
| fetch_json() | ✅ GET with JSON |
| check_url() | ✅ |
| user_agent() | ✅ |
| random_object_id() | ✅ |
| extra_inboxes() | ✅ (hook for app to add recipients) |
| is_from_outbox() | ✅ |
| parse_collection() | ✅ |

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

1. **Extended Activities** - Flag (moderation), Move (migration), Join, Leave, etc.
2. **Per-object Likes/Shares collections** - Library helpers for `Likes` and `Shares` collections
3. **Featured Collection** - For profile pages (`toot:featured`)
4. **Backward Pagination** - `prev` link support in collection pagination

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

1. **Extended Activities** - Join, Leave, View, Listen, Read, Write, Travel, Arrive
2. **per-object Likes/Shares** - Activity collections on objects
3. **Replies Collection** - Threaded conversations
4. **Replay Attack Prevention** - Verify Date header freshness
5. **Origin Verification** - Verify activity origin
6. **Content Security Policy** - Explicit CSP headers

---

## Compliance Checklist

### Library vs App Responsibilities

| Requirement | Status | Responsibility |
|-------------|--------|----------------|
| Client to Server API | ✅ | Library + App |
| Server to Server API | ⚠️ Partial | Library computes, App delivers |
| Inbox processing | ⚠️ Partial | App implements via `InboxPlugin` |
| Outbox processing | ⚠️ Partial | App implements via `CollectionPlugin` |
| WebFinger support | ✅ | Library |
| HTTP Signatures | ✅ | Library (`httpsig.py`) |
| LD Signatures | ✅ | Library (`linked_data_sig.py`) |
| JSON-LD support | ✅ | Library |

### Object Requirements

| Requirement | Status |
|-------------|--------|
| Actor types | ✅ All |
| Activity types (core) | ✅ All |
| Activity types (extended) | ❌ Most missing |
| Object types | ✅ All |
| Properties validation | ✅ |
| Collection support | ⚠️ Partial |

### Security Requirements

| Requirement | Status |
|-------------|--------|
| HTTP Signature generation | ✅ |
| HTTP Signature verification | ✅ |
| LD Signature | ✅ |
| Input validation | ✅ |
| Output sanitization | ✅ |
| Authentication | ✅ |
| Authorization | ⚠️ Partial |
| bto/bcc handling | ❌ |

### Federation Requirements

| Requirement | Status | Responsibility |
|-------------|--------|----------------|
| Actor discovery | ✅ | Library (via `fetch_iri`) |
| Content distribution | ⚠️ Partial | App implements `deliver_activity()` |
| Follower management | ✅ | Library + App |
| Block handling | ✅ | Library |
| Error handling | ✅ | Library |
| Deduplication | ❌ | App via `is_duplicate()` |

---

## References

1. [ActivityPub Specification](https://www.w3.org/TR/activitypub/)
2. [ActivityStreams 2.0](https://www.w3.org/TR/activitystreams-core/)
3. [JSON-LD 1.0](https://www.w3.org/TR/json-ld/)
4. [HTTP Signatures Draft](https://tools.ietf.org/html/draft-cavage-http-signatures-12)
5. [WebFinger RFC](https://tools.ietf.org/html/rfc7033)
