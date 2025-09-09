# Active Boxes Modernization Plan

## Project Overview
Active Boxes is a fork of Little Boxes, a tiny ActivityPub framework written in Python. The project is database and server agnostic, providing core ActivityPub functionality including:
- ActivityStreams helper classes with Outbox/Inbox abstractions
- Content helper using Markdown
- Key (RSA) helper
- HTTP signature helper
- JSON-LD signature helper
- Webfinger helper

## Current Status
The project has already undergone some basic modernization:
- Migrated from `setup.py` to `pyproject.toml`
- Moved development dependencies to `pyproject.toml`
- Switched to Poetry for dependency management and building

## Modernization Goals

### 1. Python Version Support
- **Target**: Python 3.10+ (leveraging modern features)
- **Current**: Python 3.6+ (as specified in pyproject.toml)

### 2. Code Modernization
- Leverage Python 3.10+ features:
  - Structural Pattern Matching (match/case statements)
  - Better type hinting with union types (X | Y syntax)
  - Parenthesized context managers
  - Improved performance and memory efficiency
- Full type hinting coverage
- Modern coding style and formatting
- Refactor legacy patterns to modern Python idioms

### 3. Testing Infrastructure
- Create comprehensive test suite
- Test against latest ActivityPub protocol and APIs
- Implement integration tests with real ActivityPub servers
- Add mocking for external API calls
- Improve test coverage and quality

### 4. Dependency Updates
- Update all dependencies to modern versions
- Remove deprecated or unmaintained dependencies
- Ensure compatibility with Python 3.10+

## Implementation Plan

### Phase 1: Infrastructure and Setup (Week 1)
1. Update `pyproject.toml` to require Python 3.10+
2. Update development dependencies to modern versions
3. Configure modern tooling:
   - Black (code formatting)
   - Flake8/PyLint (linting)
   - MyPy (type checking)
   - Isort (import sorting)
4. Set up CI/CD pipeline
5. Configure pre-commit hooks

### Phase 2: Code Modernization (Weeks 2-3)
1. Update all type hints to use modern syntax (X | Y instead of Union[X, Y])
2. Implement structural pattern matching where appropriate
3. Refactor legacy code patterns to modern Python idioms
4. Add comprehensive type hints throughout the codebase
5. Modernize exception handling
6. Update docstrings to modern standards

### Phase 3: Testing Enhancement (Weeks 4-5)
1. Audit current test coverage
2. Add missing unit tests
3. Create integration tests for ActivityPub protocol compliance
4. Set up mocking for external API calls
5. Implement test fixtures for common scenarios
6. Add property-based testing where appropriate

### Phase 4: Protocol Compliance and Features (Weeks 6-7)
1. Audit ActivityPub protocol implementation
2. Update to latest ActivityPub specification
3. Add support for newer ActivityPub features
4. Implement comprehensive error handling
5. Add logging and monitoring capabilities

### Phase 5: Documentation and Release (Week 8)
1. Update documentation
2. Create usage examples
3. Write migration guide
4. Prepare for first stable release
5. Publish to PyPI

## Detailed Task Breakdown

### Task 1: Update Python Version Requirements
- Update `pyproject.toml` to require Python 3.10+
- Update classifiers in `pyproject.toml`
- Remove Python < 3.10 compatibility code

### Task 2: Modernize Type Hinting
- Replace `Union[X, Y]` with `X | Y` syntax
- Replace `Optional[X]` with `X | None` syntax
- Add type hints to all functions and methods
- Use `typing_extensions` for newer typing features if needed

### Task 3: Implement Structural Pattern Matching
- Identify areas where match/case statements would improve readability
- Replace complex if/elif chains with pattern matching
- Replace isinstance checks with pattern matching where appropriate

### Task 4: Refactor Legacy Code Patterns
- Replace old string formatting with f-strings
- Use walrus operator (:=) where appropriate
- Use modern context manager syntax
- Replace manual resource management with context managers

### Task 5: Enhance Testing Suite
- Add tests for all ActivityPub object types
- Create tests for protocol compliance
- Add tests for error conditions
- Implement mock servers for integration testing
- Add performance tests

### Task 6: Update Dependencies
- Audit all dependencies for security and maintenance status
- Update to latest compatible versions
- Replace deprecated dependencies
- Add new dependencies for enhanced functionality

### Task 7: Improve Documentation
- Update README with modern usage examples
- Add API documentation
- Create comprehensive examples
- Document ActivityPub compliance

## Success Criteria
1. Full Python 3.10+ compatibility
2. 100% type hinting coverage
3. Comprehensive test suite with >90% coverage
4. ActivityPub protocol compliance with latest specification
5. Modern, readable, maintainable codebase
6. Proper documentation and usage examples
7. Published to PyPI as a stable release

## Risk Mitigation
1. Maintain backward compatibility where possible
2. Implement changes incrementally with thorough testing
3. Keep detailed documentation of changes
4. Engage with community for feedback
5. Monitor for security vulnerabilities in dependencies