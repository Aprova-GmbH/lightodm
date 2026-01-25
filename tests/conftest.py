"""
Pytest configuration and fixtures for lightodm tests.

- Unit tests: Use mongomock fixtures (no MongoDB required)
- Integration tests: Use real MongoDB via environment variables (required)
"""

import mongomock
import pytest

from lightodm.connection import MongoConnection


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client using mongomock."""
    return mongomock.MongoClient()


@pytest.fixture
def mock_db(mock_mongo_client):
    """Get a mock database."""
    return mock_mongo_client.test_db


@pytest.fixture
def mock_collection(mock_db):
    """Get a mock collection."""
    return mock_db.test_collection


class AsyncMockCollection:
    """
    Async wrapper around a mongomock collection.

    Provides async-compatible methods that delegate to the underlying
    sync mongomock collection, allowing tests to run without MongoDB.
    """

    def __init__(self, sync_collection):
        self._collection = sync_collection

    async def find_one(self, filter, *args, **kwargs):
        """Async find_one - delegates to sync collection."""
        return self._collection.find_one(filter, *args, **kwargs)

    async def replace_one(self, filter, replacement, *args, **kwargs):
        """Async replace_one - delegates to sync collection."""
        return self._collection.replace_one(filter, replacement, *args, **kwargs)

    async def delete_one(self, filter, *args, **kwargs):
        """Async delete_one - delegates to sync collection."""
        return self._collection.delete_one(filter, *args, **kwargs)

    async def update_one(self, filter, update, *args, **kwargs):
        """Async update_one - delegates to sync collection."""
        return self._collection.update_one(filter, update, *args, **kwargs)

    async def count_documents(self, filter, *args, **kwargs):
        """Async count_documents - delegates to sync collection."""
        return self._collection.count_documents(filter, *args, **kwargs)

    def find(self, filter, *args, **kwargs):
        """
        Returns an async cursor wrapper.

        Motor's find() is sync but returns an async cursor,
        so we return a wrapper with async to_list().
        """
        cursor = self._collection.find(filter, *args, **kwargs)
        return AsyncMockCursor(cursor)


class AsyncMockCursor:
    """Async wrapper around a mongomock cursor."""

    def __init__(self, cursor):
        self._cursor = cursor

    async def to_list(self, length=None):
        """Async to_list - returns all documents."""
        return list(self._cursor)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._cursor)
        except StopIteration:
            raise StopAsyncIteration from None


@pytest.fixture
def async_mock_collection(mock_db):
    """
    Get an async-compatible mock collection.

    Returns an AsyncMockCollection that wraps a mongomock collection,
    providing async methods for use in async tests.
    """

    def get_collection(name):
        return AsyncMockCollection(mock_db[name])

    return get_collection


@pytest.fixture(autouse=True)
def reset_connection():
    """Reset MongoConnection singleton between tests."""
    # Reset the singleton instance
    MongoConnection._instance = None
    MongoConnection._client = None
    MongoConnection._db = None
    MongoConnection._async_client = None
    yield
    # Clean up after test
    if MongoConnection._instance:
        MongoConnection._instance.close_connection()


@pytest.fixture
async def cleanup_test_collections():
    """
    Cleanup fixture for integration tests.
    Drops all test collections after each integration test.
    """
    yield
    # Cleanup after test
    try:
        from lightodm.connection import get_async_database
        db = await get_async_database()
        collections = await db.list_collection_names()
        for collection_name in collections:
            await db[collection_name].delete_many({})
    except Exception:
        # If MongoDB not available, that's fine (integration test would have failed anyway)
        pass
