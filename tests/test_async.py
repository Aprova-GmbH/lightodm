"""Tests for async operations in lightodm."""

import pytest
from lightodm import MongoBaseModel


class AsyncTestModel(MongoBaseModel):
    """Test model for async operations."""

    class Settings:
        name = "async_test_collection"

    name: str
    value: int


@pytest.mark.asyncio
async def test_async_save_and_get(mock_db):
    """Test async save and get operations."""
    # Override async collection to use mock
    original_method = AsyncTestModel.get_async_collection

    async def mock_get_collection():
        return mock_db[AsyncTestModel.Settings.name]

    AsyncTestModel.get_async_collection = mock_get_collection

    try:
        # Create and save
        model = AsyncTestModel(name="async_test", value=42)
        doc_id = await model.asave()

        assert doc_id == model.id

        # Retrieve
        retrieved = await AsyncTestModel.aget(doc_id)
        assert retrieved is not None
        assert retrieved.name == "async_test"
        assert retrieved.value == 42
    finally:
        AsyncTestModel.get_async_collection = original_method


@pytest.mark.asyncio
async def test_async_find(mock_db):
    """Test async find operations."""
    original_method = AsyncTestModel.get_async_collection

    async def mock_get_collection():
        return mock_db[AsyncTestModel.Settings.name]

    AsyncTestModel.get_async_collection = mock_get_collection

    try:
        # Create multiple documents
        models = [
            AsyncTestModel(name=f"test_{i}", value=i)
            for i in range(5)
        ]

        for model in models:
            await model.asave()

        # Find all
        results = await AsyncTestModel.afind({})
        assert len(results) == 5

        # Find with filter
        results = await AsyncTestModel.afind({"value": {"$gte": 3}})
        assert len(results) == 2
    finally:
        AsyncTestModel.get_async_collection = original_method


@pytest.mark.asyncio
async def test_async_delete(mock_db):
    """Test async delete operation."""
    original_method = AsyncTestModel.get_async_collection

    async def mock_get_collection():
        return mock_db[AsyncTestModel.Settings.name]

    AsyncTestModel.get_async_collection = mock_get_collection

    try:
        # Create and save
        model = AsyncTestModel(name="to_delete", value=100)
        await model.asave()

        # Verify it exists
        retrieved = await AsyncTestModel.aget(model.id)
        assert retrieved is not None

        # Delete
        deleted = await model.adelete()
        assert deleted is True

        # Verify it's gone
        retrieved = await AsyncTestModel.aget(model.id)
        assert retrieved is None
    finally:
        AsyncTestModel.get_async_collection = original_method


@pytest.mark.asyncio
async def test_async_update(mock_db):
    """Test async update operations."""
    original_method = AsyncTestModel.get_async_collection

    async def mock_get_collection():
        return mock_db[AsyncTestModel.Settings.name]

    AsyncTestModel.get_async_collection = mock_get_collection

    try:
        # Create initial document
        model = AsyncTestModel(name="original", value=10)
        await model.asave()

        # Update
        success = await AsyncTestModel.aupdate_one(
            {"_id": model.id},
            {"$set": {"value": 20}}
        )
        assert success is True

        # Verify update
        retrieved = await AsyncTestModel.aget(model.id)
        assert retrieved.value == 20
    finally:
        AsyncTestModel.get_async_collection = original_method


@pytest.mark.asyncio
async def test_async_count(mock_db):
    """Test async count operation."""
    original_method = AsyncTestModel.get_async_collection

    async def mock_get_collection():
        return mock_db[AsyncTestModel.Settings.name]

    AsyncTestModel.get_async_collection = mock_get_collection

    try:
        # Create documents
        for i in range(3):
            model = AsyncTestModel(name=f"count_test_{i}", value=i)
            await model.asave()

        # Count all
        count = await AsyncTestModel.acount()
        assert count == 3

        # Count with filter
        count = await AsyncTestModel.acount({"value": {"$gt": 0}})
        assert count == 2
    finally:
        AsyncTestModel.get_async_collection = original_method
