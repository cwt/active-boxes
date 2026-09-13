---
type: plan
title: Active Boxes Modernization Plan
description: Merged master plan for the Little Boxes fork modernization (infrastructure, Python 3.10+, testing, protocol compliance, release) with timeline and remaining work.
sources:
  - documents/MODERNIZE_PLAN.md
  - documents/IMPLEMENTATION_PLAN.md
  - documents/MODERNIZATION_SUMMARY.md
status: stable
verified: human-reviewed
stale_after: 2027-09-13T00:00:00Z
tags: [planning, modernization, activitypub, roadmap]
timestamp: 2026-09-13T00:00:00Z
---

# Active Boxes Modernization Plan

> Merged from the former `MODERNIZE_PLAN.md`, `IMPLEMENTATION_PLAN.md`, and `MODERNIZATION_SUMMARY.md`. For live compliance state, see [activitypub-compliance.md](activitypub-compliance.md).

## Project Overview

Active Boxes is a fork of Little Boxes, a tiny ActivityPub framework written in Python. The project is database and server agnostic, providing core ActivityPub functionality including:

- ActivityStreams helper classes with Outbox/Inbox abstractions
- Content helper using Markdown
- Key (RSA) helper
- HTTP signature helper
- JSON-LD signature helper
- Webfinger helper

## Current Status

Modernization Complete, but ActivityPub Compliance Gaps Remain.

The project has been successfully modernized with planned infrastructure improvements:

- Migrated from `setup.py` to `pyproject.toml` [x]
- Moved development dependencies to `pyproject.toml` [x]
- Switched to Poetry for dependency management and building [x]
- Updated to require Python 3.10+ [x]
- Modernized codebase to leverage Python 3.10+ features [x]
- Created comprehensive test suite (~89% coverage) [x]
- **ActivityPub protocol compliance: PARTIAL** [-]

## Goals

| Goal | Status |
|------|--------|
| Modernize codebase to leverage Python 3.10+ features | [x] COMPLETED |
| Create comprehensive test suite with ~89% coverage | [x] COMPLETED |
| Ensure full ActivityPub protocol compliance | [-] PARTIAL |
| Update documentation and examples | [-] PARTIAL |
| Prepare for stable release | [-] IN PROGRESS |

## Modernization Achievements

### 1. Python Version Support

- **Target**: Python 3.10+ (fully leveraged modern features) [x]
- **Current**: Python 3.10+ (as specified in pyproject.toml) [x]

Details: [python-310-modernization.md](python-310-modernization.md).

### 2. Code Modernization [x] COMPLETED

- Structural Pattern Matching (match/case statements) - IMPLEMENTED
- Better type hinting with union types (X | Y syntax) - IMPLEMENTED
- Parenthesized context managers - IMPLEMENTED
- Improved performance and memory efficiency - ACHIEVED
- Full type hinting coverage - 100% COMPLETED
- Modern coding style and formatting - ACHIEVED
- Refactored legacy patterns to modern Python idioms - COMPLETED

### 3. Testing Infrastructure [x] COMPLETED

- Comprehensive test suite - COMPLETED
- Tested against latest ActivityPub protocol and APIs - COMPLETED
- Integration tests with mock servers - COMPLETED
- Mocking for external API calls - COMPLETED
- Test coverage and quality - ACHIEVED ~89% coverage

Details: [test-suite.md](test-suite.md).

### 4. Dependency Updates [x] COMPLETED

- All dependencies updated to modern versions - COMPLETED
- Deprecated or unmaintained dependencies removed - COMPLETED
- Compatibility with Python 3.10+ - ACHIEVED

## Phases

### Phase 1: Infrastructure and Setup [x] COMPLETED

1. Updated `pyproject.toml` to require Python 3.10+ - COMPLETED
2. Updated development dependencies to modern versions - COMPLETED
3. Configured modern tooling:
   - Black (code formatting) - CONFIGURED
   - Ruff (linting) - CONFIGURED
   - MyPy (type checking) - CONFIGURED
   - Isort (import sorting) - CONFIGURED
4. Set up CI/CD pipeline - CONFIGURED
5. Configured pre-commit hooks - CONFIGURED
6. Updated README with modernization status - COMPLETED

#### Deliverables — Phase 1: Infrastructure and Setup

- Updated `pyproject.toml` with Python 3.10+ requirements
- Modern development environment
- CI/CD pipeline configuration
- Pre-commit hook configuration

### Phase 2: Code Modernization [x] COMPLETED

1. Updated all type hints to modern syntax (`X | Y` instead of `Union[X, Y]`) - COMPLETED
2. Implemented structural pattern matching where appropriate - COMPLETED
3. Refactored legacy code patterns to modern Python idioms - COMPLETED
4. Added comprehensive type hints throughout the codebase - COMPLETED
5. Modernized exception handling - COMPLETED
6. Updated docstrings to modern standards - COMPLETED

#### Key Areas

- `activitypub.py`: Core ActivityPub classes
- `backend.py`: Backend abstraction
- `content_helper.py`: Content processing utilities
- `httpsig.py`: HTTP signature handling
- `key.py`: Key management
- `linked_data_sig.py`: JSON-LD signature handling
- `webfinger.py`: WebFinger protocol implementation
- `collection.py`: Collection handling
- `urlutils.py`: URL utilities
- `errors.py`: Error definitions

#### Deliverables — Phase 2: Code Modernization

- Fully modernized codebase with Python 3.10+ features
- 100% type hinting coverage
- Improved code readability and maintainability

### Phase 3: Testing Enhancement [x] COMPLETED

1. Audited current test coverage - COMPLETED
2. Added missing unit tests - COMPLETED
3. Created integration tests for ActivityPub protocol compliance - COMPLETED
4. Set up mocking for external API calls - COMPLETED
5. Implemented test fixtures for common scenarios - COMPLETED
6. Added property-based testing where appropriate - COMPLETED

#### Test Areas

- ActivityPub object creation and validation
- Activity processing and side effects
- Collection management
- HTTP signature generation and verification
- JSON-LD signature handling
- WebFinger lookups
- Backend implementation
- Content processing

#### Deliverables — Phase 3: Testing Enhancement

- Comprehensive test suite with ~89% coverage
- Integration tests for protocol compliance
- Property-based tests for robustness
- Performance benchmarks

### Phase 4: Protocol Compliance and Features [-] PARTIAL

#### Completed

1. Audited ActivityPub protocol implementation - COMPLETED
2. Updated to latest ActivityPub specification - COMPLETED
3. Implemented comprehensive error handling - COMPLETED
4. Added logging and monitoring capabilities - COMPLETED
5. [x] **Extended Activity Types** - Flag, Move, Join, Leave, View, Listen, Read, Write, Travel, Arrive IMPLEMENTED

#### Compliance Areas

| Area | Status | Notes |
|------|--------|-------|
| Server implementation | [-] Partial | No delivery POST method |
| Object/Activity types | [x] Complete | Core complete, extended now complete |
| Collection management | [-] Partial | Basic done, pagination incomplete |
| HTTP signatures | [x] | Generation/verification work |
| JSON-LD/Context | [x] | Core done |
| WebFinger | [x] | Full support |
| Security | [-] Partial | Signatures done, bto/bcc not stripped |
| Federation | [-] Partial | No delivery, no deduplication |

#### Remaining Phase 4 Work

1. **Backend Delivery** - No POST method for server-to-server delivery
2. **Deduplication** - No inbox deduplication by activity ID
3. **Retry Logic** - No exponential backoff for failed deliveries
4. **HTTP Signature Integration** - httpsig.py exists but not integrated into delivery
5. **Missing Collections** - [x] Shares, Likes (per-object), Featured, Replies IMPLEMENTED (v0.2.0)
6. **bto/bcc Handling** - Not stripped per spec

#### Deliverables — Phase 4: Protocol Compliance and Features

- Core ActivityPub compliant implementation [x]
- Comprehensive error handling [x]
- Logging and monitoring capabilities [x]
- **Full federation: MISSING** [ ]

### Phase 5: Documentation and Release [-] PARTIAL

1. Updated documentation - COMPLETED (v0.2.0)
2. Created usage examples - COMPLETED
3. Written migration guide - COMPLETED
4. Prepared for first stable release - PARTIAL
5. Published to PyPI - COMPLETED

#### Documentation Areas

- API documentation - COMPLETED
- Usage examples - COMPLETED
- Migration guide from Little Boxes - COMPLETED
- ActivityPub compliance documentation - UPDATED
- Testing documentation - COMPLETED
- Contribution guidelines - COMPLETED

#### Deliverables — Phase 5: Documentation and Release

- Complete documentation - **PARTIAL**
- Usage examples - COMPLETED
- Migration guide - COMPLETED
- Stable release published to PyPI - COMPLETED

## Detailed Tasks

### Task 1: Update Python Version Requirements [x] COMPLETED

- Updated `pyproject.toml` to require Python 3.10+ - COMPLETED
- Updated classifiers in `pyproject.toml` - COMPLETED
- Removed Python < 3.10 compatibility code - COMPLETED

### Task 2: Modernize Type Hinting [x] COMPLETED

- Replaced `Union[X, Y]` with `X | Y` syntax - COMPLETED
- Replaced `Optional[X]` with `X | None` syntax - COMPLETED
- Added type hints to all functions and methods - COMPLETED
- Used `typing_extensions` for newer typing features where needed - COMPLETED

### Task 3: Implement Structural Pattern Matching [x] COMPLETED

- Identified areas where match/case statements would improve readability - COMPLETED
- Replaced complex if/elif chains with pattern matching - COMPLETED
- Replaced isinstance checks with pattern matching where appropriate - COMPLETED

### Task 4: Refactor Legacy Code Patterns [x] COMPLETED

- Replaced old string formatting with f-strings - COMPLETED
- Used walrus operator (:=) where appropriate - COMPLETED
- Used modern context manager syntax - COMPLETED
- Replaced manual resource management with context managers - COMPLETED

### Task 5: Enhance Testing Suite [x] COMPLETED

- Added tests for all ActivityPub object types - COMPLETED
- Created tests for protocol compliance - COMPLETED
- Added tests for error conditions - COMPLETED
- Implemented mock servers for integration testing - COMPLETED
- Added performance tests - COMPLETED

### Task 6: Update Dependencies [x] COMPLETED

- Audited all dependencies for security and maintenance status - COMPLETED
- Updated to latest compatible versions - COMPLETED
- Replaced deprecated dependencies - COMPLETED
- Added new dependencies for enhanced functionality - COMPLETED

### Task 7: Improve Documentation [x] COMPLETED (v0.2.0)

- Updated README with modern usage examples - COMPLETED
- Added API documentation - COMPLETED
- Created comprehensive examples - COMPLETED
- Documented ActivityPub compliance - COMPLETED

## Timeline

| Week | Phase | Key Deliverables | Status |
|------|-------|------------------|--------|
| 1 | Infrastructure and Setup | Updated dependencies, CI/CD, development environment | [x] COMPLETED |
| 2-3 | Code Modernization | Python 3.10+ features, type hints, refactored code | [x] COMPLETED |
| 4-5 | Testing Enhancement | Comprehensive test suite, integration tests | [x] COMPLETED |
| 6-7 | Protocol Compliance | ActivityPub compliance, error handling, security | [-] PARTIAL |
| 8 | Documentation and Release | Documentation, examples, stable release | [-] PARTIAL |
| 9-10 | **Remaining Work** | **Federation delivery, deduplication** | **TODO** |

## Remaining Work

### High Priority

| Feature | Description | File(s) |
|---------|-------------|----------|
| Delivery method | Add `deliver()` to Backend for POST to remote inboxes | backend.py |
| HTTP Sig integration | Sign outgoing delivery requests | backend.py, httpsig.py |
| Inbox deduplication | Track seen activity IDs | backend.py |
| Retry logic | Exponential backoff for failed deliveries | backend.py |
| bto/bcc stripping | Remove before delivery per spec | activitypub.py |
| [x] Flag activity | Moderation/reporting | activitypub.py |
| [x] Move activity | Actor migration | activitypub.py |

### Medium Priority

| Feature | Description | File(s) |
|---------|-------------|----------|
| [x] Backward pagination | Support prev link in collections (v0.2.0) | collection.py |
| [x] streams property | Supplementary collections (v0.2.0) | activitypub.py |
| [x] Featured collection | Profile pages (v0.2.0) | activitypub.py |
| [x] per-object Likes | Likes collection on objects (v0.2.0) | activitypub.py |
| [x] per-object Shares | Shares collection on objects (v0.2.0) | activitypub.py |
| [x] Replies collection | Threaded conversations (v0.2.0) | activitypub.py |

### Low Priority

| Feature | Description | File(s) |
|---------|-------------|----------|
| [x] Extended activities | Join, Leave, View, Listen, Read, Write, Travel, Arrive | activitypub.py |
| [x] Replay prevention | Verify Date header freshness (v0.2.0) | http_client.py |
| Origin verification | Verify activity origin (app hook) | activitypub.py |
| [x] CSP headers | Content Security Policy (v0.2.0) | http_client.py |

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Full Python 3.10+ compatibility | [x] | [x] ACHIEVED |
| 100% type hinting coverage | [x] | [x] ACHIEVED |
| Comprehensive test suite with ~89% coverage | [x] | [x] ACHIEVED |
| Full ActivityPub protocol compliance | [x] | [-] PARTIAL |
| Modern, readable, maintainable codebase | [x] | [x] ACHIEVED |
| Proper documentation and usage examples | [x] | [x] ACHIEVED (v0.2.0) |
| Published to PyPI as a stable release | [x] | [x] ACHIEVED |

## Resources Needed

1. Development environment with Python 3.10+ [x]
2. Access to ActivityPub test servers for integration testing [x]
3. Code review tools [x]
4. CI/CD pipeline access [x]
5. PyPI account for publishing [x]

## Monitoring and Evaluation

1. Weekly progress reviews - [x] CONDUCTED
2. Code quality metrics (coverage, linting, type checking) - [x] MONITORED
3. Performance benchmarks - [x] CONDUCTED
4. Security scans - [x] PERFORMED
5. Community feedback - [-] IN PROGRESS

## Risk Mitigation

1. Maintained backward compatibility where possible - [x] IMPLEMENTED
2. Implemented changes incrementally with thorough testing - [x] IMPLEMENTED
3. Kept detailed documentation of changes - [-] NEEDS UPDATE
4. Engaged with community for feedback - [-] IN PROGRESS
5. Monitored for security vulnerabilities in dependencies - [x] IMPLEMENTED
