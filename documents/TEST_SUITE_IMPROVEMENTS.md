# Test Suite Improvement Plan

## Current State Analysis

The project currently has a basic test suite with the following characteristics:
- Unit tests for individual modules (backend, collection, content_helper, httpsig, key, linked_data_sig, urlutils, webfinger)
- An in-memory backend implementation for testing (`InMemBackend`)
- Mock-based testing approach using `unittest.mock`
- Basic test coverage for core functionality

## Improvements Needed

### 1. Expand Test Coverage

#### ActivityPub Core Tests
- Test all Activity types (Create, Update, Delete, Follow, Accept, Reject, Like, Announce, etc.)
- Test Actor types (Person, Application, Group, Organization, Service)
- Test Collection handling
- Test Object validation
- Test Activity parsing and serialization

#### Backend Tests
- Expand `InMemBackend` to support all ActivityPub operations
- Add tests for error conditions (network failures, invalid responses, etc.)
- Test URL validation and security checks
- Test HTTP signature verification
- Test JSON-LD signature handling

#### Content Helper Tests
- Expand Markdown parsing tests
- Add tests for edge cases in hashtag and mention parsing
- Test HTML sanitization
- Test content normalization

#### Security Tests
- Test HTTP signature generation and verification
- Test JSON-LD signature generation and verification
- Test Key generation and management
- Test Webfinger lookup security

### 2. Integration Testing

#### ActivityPub Protocol Compliance
- Test against ActivityPub test suite (if available)
- Create tests that validate protocol compliance
- Test interoperability with popular ActivityPub implementations (Mastodon, Pleroma, etc.)
- Test federation scenarios

#### Mock Server Testing
- Create mock ActivityPub servers for integration testing
- Test sending and receiving activities
- Test inbox/outbox processing
- Test follower management

### 3. Modern Testing Framework Features

#### Parametrized Tests
- Use `pytest.mark.parametrize` for testing multiple scenarios
- Create test matrices for different Activity types and configurations

#### Fixtures
- Create reusable fixtures for common test scenarios
- Use `pytest.fixture` for setup/teardown
- Create fixtures for different ActivityPub objects

#### Property-Based Testing
- Use `hypothesis` for property-based testing
- Generate random ActivityPub objects for testing
- Test robustness against malformed inputs

### 4. Test Organization

#### Test Structure
- Organize tests by module/functionality
- Create separate directories for unit, integration, and protocol compliance tests
- Use clear naming conventions

#### Test Data Management
- Create standardized test data fixtures
- Use factory patterns for creating test objects
- Manage test data lifecycle

### 5. Test Quality Improvements

#### Assertions
- Use more specific assertions
- Add custom assertion helpers for ActivityPub objects
- Improve error messages for failing tests

#### Test Isolation
- Ensure tests are properly isolated
- Clean up test data between tests
- Use temporary directories for file-based tests

#### Performance
- Optimize slow tests
- Use parallel test execution
- Profile test suite performance

## Implementation Plan

### Phase 1: Test Infrastructure (Week 1)
1. Set up pytest configuration
2. Configure test coverage reporting
3. Set up continuous integration for tests
4. Create basic test fixtures

### Phase 2: Expand Unit Test Coverage (Weeks 2-3)
1. Add missing unit tests for all modules
2. Improve existing test quality
3. Add edge case testing
4. Add error condition testing

### Phase 3: Integration Testing (Weeks 4-5)
1. Create mock ActivityPub servers
2. Implement protocol compliance tests
3. Add federation scenario tests
4. Test interoperability with popular implementations

### Phase 4: Advanced Testing Features (Weeks 6-7)
1. Implement property-based testing
2. Add performance tests
3. Implement security-focused tests
4. Add stress testing

### Phase 5: Documentation and Maintenance (Week 8)
1. Document test suite structure
2. Create contributor guidelines for testing
3. Set up automated test reporting
4. Establish test maintenance procedures

## Specific Test Areas to Address

### ActivityPub Object Tests
- Test creation of all Activity types
- Test validation of required fields
- Test parsing of complex objects
- Test serialization/deserialization

### Backend Tests
- Test all abstract methods are properly implemented
- Test error handling in fetch_iri
- Test URL validation
- Test user agent generation

### Content Helper Tests
- Test Markdown processing edge cases
- Test hashtag extraction and linking
- Test mention extraction and linking
- Test HTML sanitization

### Security Tests
- Test HTTP signature end-to-end
- Test JSON-LD signature end-to-end
- Test key management
- Test webfinger security

### Protocol Compliance Tests
- Test ActivityPub protocol requirements
- Test HTTP header requirements
- Test content type requirements
- Test error response formats

## Tools and Libraries to Consider

1. **pytest** - Modern testing framework (already in use)
2. **pytest-cov** - Coverage reporting (already in use)
3. **hypothesis** - Property-based testing
4. **pytest-mock** - Improved mocking integration
5. **responses** - Mock HTTP responses
6. **freezegun** - Time manipulation for tests
7. **factory_boy** - Test data generation
8. **tox** - Test automation across Python versions

## Success Metrics

1. >90% code coverage
2. All ActivityPub protocol requirements tested
3. Integration tests with mock servers
4. Property-based tests for core functionality
5. Performance benchmarks established
6. Security-focused test suite
7. Clear test documentation
8. Fast test execution (< 1 minute for full suite)