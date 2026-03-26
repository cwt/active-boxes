# Active Boxes (Modernized Little Boxes)

This project is a fork of [Little Boxes](https://github.com/tsileo/little-boxes) that has been modernized and relicensed from ISC to MIT.

⚠️ **Modernization Complete, ActivityPub Compliance In Progress** ⚠️

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
- [~] ActivityPub protocol compliance - Core 11 activities ✅, Extended activities ⚠️
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
- Comprehensive test suite with ~89% coverage
- Modern code formatting with Black
- Strict linting with Ruff
- Type checking with MyPy

### Testing

- ActivityPub protocol compliance testing (core activities)
- Integration tests with mock servers
- Property-based testing for robustness
- Security-focused test suite (~89% coverage)

## Implemented ActivityPub Features

### Core Activities ✅

Create, Update, Delete, Follow, Accept, Reject, Add, Remove, Like, Block, Undo, Announce

### Actor Properties ✅

inbox, outbox, following, followers, preferredUsername, endpoints (sharedInbox)

### Collections ✅

Collection, OrderedCollection, CollectionPage, OrderedCollectionPage

### Security ✅

HTTP Signatures (generation/verification), Linked Data Signatures

### Missing (Under Development)

- Extended activities: Flag, Move, Join, Leave, View, Listen, Read, Write, Travel, Arrive
- Server-to-server delivery (POST to remote inboxes)
- Inbox deduplication
- Retry logic with exponential backoff
- Per-object Likes/Shares collections

## Modernization Plans

Detailed planning documents have been created to guide the modernization effort:

- [MODERNIZE_PLAN.md](documents/MODERNIZE_PLAN.md) - Overall modernization strategy
- [PYTHON_310_MODERNIZATION.md](documents/PYTHON_310_MODERNIZATION.md) - Python 3.10+ feature implementation
- [TEST_SUITE_IMPROVEMENTS.md](documents/TEST_SUITE_IMPROVEMENTS.md) - Test suite enhancement plans
- [ACTIVITYPUB_COMPLIANCE.md](documents/ACTIVITYPUB_COMPLIANCE.md) - ActivityPub protocol compliance requirements
- [IMPLEMENTATION_PLAN.md](documents/IMPLEMENTATION_PLAN.md) - Detailed 8-week implementation timeline

## Original Project

For information about the original project, please refer to [ORIGINAL-README.md](ORIGINAL-README.md).
