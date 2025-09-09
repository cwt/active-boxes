# ActivityPub Protocol Compliance Requirements

## Overview

ActivityPub is a decentralized social networking protocol based on the ActivityStreams 2.0 data format. It provides a client to server API for creating, updating and deleting content, as well as a federated server to server API for delivering notifications and content.

## Core Protocol Requirements

### 1. Server Implementation

#### 1.1. Client to Server Interactions
- **Create**: Clients can submit new activities to the server
- **Update**: Clients can update existing objects
- **Delete**: Clients can delete objects
- **Follow**: Clients can follow other actors
- **Undo**: Clients can undo previous activities

#### 1.2. Server to Server Interactions
- **Delivery**: Servers deliver activities to target actors' inboxes
- **Inbox**: Servers receive and process activities from other servers
- **Outbox**: Servers expose activities performed by actors
- **Follow**: Servers handle follow requests and notifications

### 2. Objects and Activities

#### 2.1. Required Object Types
- **Actor Types**:
  - Person
  - Application
  - Group
  - Organization
  - Service
  
- **Activity Types**:
  - Create
  - Update
  - Delete
  - Follow
  - Accept
  - Reject
  - Add
  - Remove
  - Like
  - Announce
  - Undo
  
- **Object Types**:
  - Note
  - Article
  - Image
  - Video
  - Audio
  - Document
  - Page
  - Event
  - Place
  - Profile
  - Relationship
  - Tombstone

#### 2.2. Required Properties
- **id**: Globally unique identifier
- **type**: Object type
- **actor**: Actor performing the activity
- **object**: Object of the activity
- **published**: Timestamp of publication
- **to**: Primary audience
- **cc**: Secondary audience
- **audience**: Target audience

### 3. Collections

#### 3.1. Ordered Collections
- Support for OrderedCollection and OrderedCollectionPage
- Proper pagination implementation
- Consistent ordering

#### 3.2. Collection Management
- Adding and removing items
- Collection validation
- Collection serialization

### 4. HTTP Signatures

#### 4.1. Signature Generation
- Proper signature header generation
- Correct digest calculation
- Key management

#### 4.2. Signature Verification
- Header parsing and validation
- Digest verification
- Key retrieval and validation

### 5. JSON-LD and Context

#### 5.1. Context Handling
- Proper @context inclusion
- Security context support
- Extension context support

#### 5.2. Serialization
- JSON-LD serialization
- ActivityStreams 2.0 compliance
- Proper content negotiation

### 6. WebFinger

#### 6.1. Resource Lookup
- WebFinger endpoint implementation
- Actor resource discovery
- Proper response format

### 7. Security Requirements

#### 7.1. Authentication
- HTTP Signature authentication
- Token-based authentication (optional)
- Session management

#### 7.2. Authorization
- Activity visibility controls
- Audience targeting
- Privacy controls

#### 7.3. Data Validation
- Input sanitization
- Output escaping
- Content security policies

## Implementation Specifics

### 1. Inbox Processing

#### 1.1. Activity Validation
- Verify actor exists and is valid
- Validate activity type and properties
- Check signatures and authentication
- Validate object integrity

#### 1.2. Side Effects
- Update collections
- Send notifications
- Trigger additional activities
- Update search indexes

### 2. Outbox Processing

#### 2.1. Activity Creation
- Generate unique identifiers
- Set publication timestamps
- Apply visibility controls
- Add to actor's outbox

#### 2.2. Delivery
- Identify target inboxes
- Generate appropriate payloads
- Handle delivery failures
- Implement retry logic

### 3. Federation

#### 3.1. Actor Discovery
- WebFinger lookup
- Actor profile retrieval
- Key discovery

#### 3.2. Content Distribution
- Audience targeting
- Inbox delivery
- Follower management
- Block list handling

## Testing Requirements

### 1. Protocol Compliance Tests

#### 1.1. Object Creation and Validation
- Test all required object types
- Validate required properties
- Test error conditions

#### 1.2. Activity Processing
- Test all activity types
- Validate side effects
- Test error handling

#### 1.3. Collection Management
- Test collection creation
- Validate pagination
- Test item management

### 2. Security Tests

#### 2.1. Signature Verification
- Test valid signatures
- Test invalid signatures
- Test expired signatures
- Test key rotation

#### 2.2. Authentication
- Test HTTP Signature auth
- Test token-based auth
- Test unauthorized access

### 3. Interoperability Tests

#### 3.1. Popular Implementation Compatibility
- Test with Mastodon
- Test with Pleroma
- Test with PeerTube
- Test with other implementations

#### 3.2. Federation Scenarios
- Follow/unfollow workflows
- Content sharing
- Notification delivery
- Block/reject handling

## Compliance Checklist

### Server Implementation
- [ ] Client to Server API
- [ ] Server to Server API
- [ ] Inbox processing
- [ ] Outbox processing
- [ ] WebFinger support
- [ ] HTTP Signatures
- [ ] JSON-LD support

### Object Requirements
- [ ] All required actor types
- [ ] All required activity types
- [ ] All required object types
- [ ] Required properties validation
- [ ] Collection support

### Security Requirements
- [ ] HTTP Signature generation
- [ ] HTTP Signature verification
- [ ] Input validation
- [ ] Output sanitization
- [ ] Authentication
- [ ] Authorization

### Federation Requirements
- [ ] Actor discovery
- [ ] Content distribution
- [ ] Follower management
- [ ] Block handling
- [ ] Error handling

## References

1. [ActivityPub Specification](https://www.w3.org/TR/activitypub/)
2. [ActivityStreams 2.0](https://www.w3.org/TR/activitystreams-core/)
3. [JSON-LD 1.0](https://www.w3.org/TR/json-ld/)
4. [HTTP Signatures Draft](https://tools.ietf.org/html/draft-cavage-http-signatures-12)
5. [WebFinger RFC](https://tools.ietf.org/html/rfc7033)