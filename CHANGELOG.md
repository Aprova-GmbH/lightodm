# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-05

### Added
- **Composite key support** for deterministic ID generation
  - New `composite_key` setting in `Settings` class
  - IDs computed as MD5 hash of concatenated field values
  - Enables multi-tenant applications with predictable document IDs
  - New `generate_composite_id()` helper function exported from package
- Comprehensive integration tests for composite key functionality
- `CLAUDE.md` project guidance file for AI-assisted development
- Additional edge case tests improving code coverage

### Changed
- Improved API documentation formatting and clarity
- Updated test organization with clear unit/integration separation

### Fixed
- Pydantic v2.11+ deprecation warning for `model_fields` access on instances

## [0.1.0] - 2026-01-17

### Added
- Initial release of LightODM
- `MongoBaseModel` base class with full CRUD operations
- Support for both synchronous (PyMongo) and asynchronous (Motor) operations
- Thread-safe singleton connection manager (`MongoConnection`)
- Automatic cleanup with atexit handlers
- Full type hints and py.typed marker
- Pydantic v2 integration with field mapping (_id ↔ id)
- Optional connection - users can override `get_collection()` methods
- Comprehensive CRUD methods:
  - Sync: `get`, `save`, `delete`, `find`, `find_one`, `find_iter`, `count`
  - Async: `aget`, `asave`, `adelete`, `afind`, `afind_one`, `afind_iter`, `acount`
  - Update operations: `update_one`, `update_many`, `aupdate_one`, `aupdate_many`
  - Delete operations: `delete_one`, `delete_many`, `adelete_one`, `adelete_many`
  - Bulk operations: `insert_many`, `ainsert_many`
  - Aggregation: `aggregate`, `aaggregate`
- ObjectId-based ID generation with `generate_id()` function
- Settings class pattern for collection name configuration
- Support for extra fields with Pydantic's `extra='allow'`

### Features
- Zero dependencies beyond Pydantic, PyMongo, and Motor
- Simple API similar to Beanie but more lightweight
- Full async/await support
- Connection pooling with configurable parameters
- Automatic field validation via Pydantic
- Type-safe generic methods
