"""Tests for async operations in lightodm."""

import pytest

from lightodm import MongoBaseModel


class AsyncTestModel(MongoBaseModel):
    """Test model for async operations."""

    class Settings:
        name = "async_test_collection"

    name: str
    value: int


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_save_and_get(cleanup_test_collections):
    """Test async save and get operations with real MongoDB."""
    # Create and save - uses real MongoDB via environment variables
    model = AsyncTestModel(name="async_test", value=42)
    doc_id = await model.asave()

    assert doc_id == model.id

    # Retrieve - uses real MongoDB
    retrieved = await AsyncTestModel.aget(doc_id)
    assert retrieved is not None
    assert retrieved.name == "async_test"
    assert retrieved.value == 42


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find(cleanup_test_collections):
    """Test async find operations with real MongoDB."""
    # Create multiple documents
    models = [AsyncTestModel(name=f"test_{i}", value=i) for i in range(5)]

    for model in models:
        await model.asave()

    # Find all
    results = await AsyncTestModel.afind({})
    assert len(results) == 5

    # Find with filter
    results = await AsyncTestModel.afind({"value": {"$gte": 3}})
    assert len(results) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_delete(cleanup_test_collections):
    """Test async delete operation with real MongoDB."""
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_update(cleanup_test_collections):
    """Test async update operations with real MongoDB."""
    # Create initial document
    model = AsyncTestModel(name="original", value=10)
    await model.asave()

    # Update
    success = await AsyncTestModel.aupdate_one({"_id": model.id}, {"$set": {"value": 20}})
    assert success is True

    # Verify update
    retrieved = await AsyncTestModel.aget(model.id)
    assert retrieved.value == 20


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_count(cleanup_test_collections):
    """Test async count operation with real MongoDB."""
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
