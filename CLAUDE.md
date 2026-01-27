# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LightODM is a lightweight MongoDB ODM (Object-Document Mapper) built on Pydantic v2, PyMongo, and Motor. It provides a minimal alternative to Beanie with full sync/async support. The entire codebase is ~500 lines of production code across 3 core modules.

## Development Commands

### Environment Setup
```bash
# Install uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with development tools
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### Testing
```bash
# Run fast unit tests only (no MongoDB needed) - DEFAULT for local dev
uv run pytest -m unit

# Run integration tests (REQUIRES MongoDB via Docker - see setup below)
uv run pytest -m integration

# Run all tests (unit + integration - requires MongoDB)
uv run pytest

# Run with coverage
uv run pytest --cov=lightodm --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=lightodm --cov-report=html

# Run specific test file
uv run pytest tests/test_model.py

# Run specific test function
uv run pytest tests/test_model.py::test_model_creation

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### Code Quality
```bash
# Format code (line length: 100)
uv run black src tests

# Lint code
uv run ruff check src tests

# Auto-fix linting issues
uv run ruff check --fix src tests

# Check formatting without changes
uv run black --check src tests

# Type checking
uv run mypy src
```

### MongoDB Setup for Integration Testing
```bash
# Start MongoDB using Docker
docker run -d -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=test \
  -e MONGO_INITDB_ROOT_PASSWORD=test \
  --name lightodm-mongo \
  mongo:latest

# Set environment variables for integration tests
export MONGO_URL="mongodb://localhost:27017"
export MONGO_USER="test"
export MONGO_PASSWORD="test"
export MONGO_DB_NAME="test_db"

# Run integration tests
uv run pytest -m integration

# Cleanup when done
docker stop lightodm-mongo && docker rm lightodm-mongo
unset MONGO_URL MONGO_USER MONGO_PASSWORD MONGO_DB_NAME
```

**Important:**
- **Unit tests** (`pytest -m unit`) use mocks and NEVER require MongoDB
- **Integration tests** (`pytest -m integration`) REQUIRE real MongoDB and will FAIL without it
- For local development, run unit tests only (no MongoDB needed)
- For full testing, start MongoDB via Docker and run both test suites

## Architecture

### Core Components

**1. Connection Management (src/lightodm/connection.py)**
- `MongoConnection`: Thread-safe singleton managing both PyMongo and Motor clients
- Sync client initialized eagerly, async client created lazily on first async operation
- Configuration via environment variables: `MONGO_URL`, `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_DB_NAME`
- Automatic cleanup via `atexit` handler
- Global helper functions: `get_collection()`, `get_database()`, `get_async_database()`, etc.

**2. ODM Model (src/lightodm/model.py)**
- `MongoBaseModel`: Pydantic v2 base class providing CRUD operations
- Dual API: All methods have sync and async versions (async prefixed with `a`)
- `id` field automatically maps to MongoDB `_id` field
- ID generation via `generate_id()` using MongoDB ObjectId
- Supports `extra='allow'` for dynamic fields
- Collection name specified via inner `Settings` class

**3. Public API (src/lightodm/__init__.py)**
- Exports: `MongoBaseModel`, `generate_id`, connection helpers
- Single import point for all functionality

### Key Design Patterns

**ID Field Mapping**
- Pydantic models use `id` field, MongoDB uses `_id`
- `_to_mongo_dict()`: Converts model to dict with `id` -> `_id` mapping
- `_from_mongo_dict()`: Converts MongoDB doc to model with `_id` -> `id` mapping
- `_uses_mongo_id_alias()`: Checks if model explicitly uses `_id` alias (for custom ID fields)

**Dual Sync/Async Support**
- Sync methods use PyMongo and return results directly
- Async methods (prefixed with `a`) use Motor and use async/await
- Example: `save()` vs `asave()`, `find()` vs `afind()`
- Both APIs share the same singleton connection manager

**Collection Access**
- Override `get_collection()` for custom sync connection logic
- Override `get_async_collection()` for custom async connection logic
- Default implementation uses singleton connection via `Settings.name`

## Testing Strategy

**Strict Separation: Unit vs Integration**
- **Unit Tests** (`@pytest.mark.unit`): ALWAYS use mongomock, NEVER require MongoDB
  - Test model logic, serialization, validation, pure Python behavior
  - Run in ~0.02s locally and in CI
  - Location: `tests/test_model.py`

- **Integration Tests** (`@pytest.mark.integration`): REQUIRE real MongoDB, FAIL if unavailable
  - Test PyMongo/Motor integration, connection handling, real CRUD operations
  - Need `MONGO_URL`, `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_DB_NAME` env vars
  - Only run in CI or locally with MongoDB via Docker
  - Location: `tests/test_async.py`, `tests/test_connection.py`

**Test Structure (tests/)**
- `conftest.py`: Pytest fixtures (mongomock for unit tests, cleanup for integration)
- `test_model.py`: 10 unit tests - Pure model logic (no MongoDB needed)
- `test_async.py`: 5 integration tests - Async operations with real MongoDB
- `test_connection.py`: 11 integration tests - Connection manager with real MongoDB

**Test Fixtures**
- `mock_mongo_client`: mongomock client for unit tests (NOT used by integration tests)
- `async_mock_collection`: Async wrapper for unit tests (NOT used by integration tests)
- `cleanup_test_collections`: Cleanup fixture for integration tests (drops collections after test)
- `reset_connection`: Auto-cleanup fixture that resets MongoConnection singleton between tests

**CI (GitHub Actions)**
- Runs unit tests FIRST (without MongoDB env vars) → 10 tests pass
- Runs integration tests SECOND (with MongoDB service) → 16 tests pass
- Both must pass for CI to succeed
- MongoDB 7 service configured in workflow

**Coverage Requirements**
- Target: >95% code coverage
- Tests cover both sync and async paths
- Coverage combined from unit and integration test runs via `--cov-append`

## Design Philosophy & Contribution Guidelines

**Core Principles**
1. **Minimalistic**: Keep codebase small (<1000 lines)
2. **Explicit over Implicit**: No magic, clear behavior
3. **Dual Support**: Both sync and async APIs equally supported
4. **Pydantic Native**: Leverage Pydantic v2 fully
5. **MongoDB Direct**: Expose PyMongo/Motor directly, no query builders
6. **Zero Abstraction Penalty**: Minimal overhead over raw PyMongo

**What to Accept**
- Bug fixes
- Performance improvements
- Documentation improvements
- Test coverage improvements
- Small API enhancements that fit the philosophy

**What to Reject**
- Heavy abstractions (query builders, etc.)
- Features that significantly increase complexity
- Breaking changes without strong justification
- Dependencies beyond pydantic, pymongo, motor

**Code Style**
- Black formatter (line length: 100)
- Ruff linter
- Type hints for all public APIs
- Google-style docstrings for public functions/classes
- Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `style:`, `chore:`

## Common Patterns

**Defining a Model**
```python
class User(MongoBaseModel):
    class Settings:
        name = "users"  # Required: MongoDB collection name

    name: str
    email: str
    age: Optional[int] = None
```

**Custom ID Field**
```python
class Product(MongoBaseModel):
    class Settings:
        name = "products"

    id: str = Field(default_factory=generate_id, alias="_id")
    name: str
```

**Custom Connection**
```python
@classmethod
def get_collection(cls):
    client = MongoClient("mongodb://custom:27017")
    return client["custom_db"]["custom_collection"]
```

**Sync vs Async Operations**
- Sync: `save()`, `find()`, `update_one()`, `delete()`
- Async: `asave()`, `afind()`, `aupdate_one()`, `adelete()`
- Iterators: `find_iter()` (sync) vs `afind_iter()` (async)

## Important Implementation Notes

- Always test both sync and async code paths when modifying model operations
- `_to_mongo_dict()` must handle `extra` fields from `__pydantic_extra__`
- Connection singleton must be reset in tests via `reset_connection` fixture
- Motor client creation is lazy to avoid async initialization issues
- PyMongo uses `count_documents()` not deprecated `count()`
- Use `replace_one(..., upsert=True)` for save operations