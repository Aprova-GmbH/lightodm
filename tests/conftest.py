"""Pytest configuration and fixtures for lightodm tests."""

import pytest
import mongomock
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
