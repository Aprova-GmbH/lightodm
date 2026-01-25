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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find_one(cleanup_test_collections):
    """Test async find_one operation with real MongoDB."""
    # Create documents
    model1 = AsyncTestModel(name="first", value=1)
    model2 = AsyncTestModel(name="second", value=2)
    await model1.asave()
    await model2.asave()

    # Find one by filter
    result = await AsyncTestModel.afind_one({"name": "second"})
    assert result is not None
    assert result.name == "second"
    assert result.value == 2

    # Find one non-existent
    result = await AsyncTestModel.afind_one({"name": "nonexistent"})
    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find_iter(cleanup_test_collections):
    """Test async find_iter operation with real MongoDB."""
    # Create documents
    models = [AsyncTestModel(name=f"iter_{i}", value=i) for i in range(3)]
    for model in models:
        await model.asave()

    # Use async iterator
    results = []
    async for doc in AsyncTestModel.afind_iter({}):
        results.append(doc)

    assert len(results) == 3
    assert all(isinstance(r, AsyncTestModel) for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_update_many(cleanup_test_collections):
    """Test async update_many operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = AsyncTestModel(name=f"batch_{i}", value=i)
        await model.asave()

    # Update multiple
    modified_count = await AsyncTestModel.aupdate_many(
        {"value": {"$gte": 3}}, {"$set": {"name": "updated"}}
    )
    assert modified_count == 2

    # Verify updates
    results = await AsyncTestModel.afind({"name": "updated"})
    assert len(results) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_delete_one(cleanup_test_collections):
    """Test async delete_one operation with real MongoDB."""
    # Create documents
    model1 = AsyncTestModel(name="delete_me", value=1)
    model2 = AsyncTestModel(name="delete_me", value=2)
    await model1.asave()
    await model2.asave()

    # Delete one
    deleted = await AsyncTestModel.adelete_one({"name": "delete_me"})
    assert deleted is True

    # Verify only one was deleted
    count = await AsyncTestModel.acount({"name": "delete_me"})
    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_delete_one_no_match(cleanup_test_collections):
    """Test adelete_one returns False when no document matches."""
    deleted = await AsyncTestModel.adelete_one({"name": "nonexistent"})
    assert deleted is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_delete_many(cleanup_test_collections):
    """Test async delete_many operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = AsyncTestModel(name=f"batch_delete_{i}", value=i)
        await model.asave()

    # Delete multiple
    deleted_count = await AsyncTestModel.adelete_many({"value": {"$lt": 3}})
    assert deleted_count == 3

    # Verify remaining
    count = await AsyncTestModel.acount()
    assert count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_aggregate(cleanup_test_collections):
    """Test async aggregate operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = AsyncTestModel(name=f"agg_{i}", value=i)
        await model.asave()

    # Run aggregation
    pipeline = [{"$match": {"value": {"$gte": 2}}}, {"$count": "total"}]
    results = await AsyncTestModel.aaggregate(pipeline)

    assert len(results) == 1
    assert results[0]["total"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_insert_many(cleanup_test_collections):
    """Test async insert_many operation with real MongoDB."""
    # Create models
    models = [AsyncTestModel(name=f"bulk_{i}", value=i) for i in range(3)]

    # Insert many
    ids = await AsyncTestModel.ainsert_many(models)

    assert len(ids) == 3
    assert all(isinstance(id, str) for id in ids)

    # Verify all were inserted
    count = await AsyncTestModel.acount()
    assert count == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_insert_many_empty(cleanup_test_collections):
    """Test ainsert_many with empty list."""
    ids = await AsyncTestModel.ainsert_many([])
    assert ids == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_delete_without_id(cleanup_test_collections):
    """Test adelete returns False when ID is not set."""
    model = AsyncTestModel(name="test", value=1)
    model.id = None
    assert await model.adelete() is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_save_exclude_none(cleanup_test_collections):
    """Test async save with exclude_none parameter."""

    # Create model with optional field
    class ModelWithOptional(AsyncTestModel):
        optional: str = None

    model = ModelWithOptional(name="test", value=42)
    doc_id = await model.asave(exclude_none=True)

    # Verify it was saved
    retrieved = await AsyncTestModel.aget(doc_id)
    assert retrieved is not None
    assert retrieved.name == "test"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_update_one_upsert(cleanup_test_collections):
    """Test async update_one with upsert."""
    from lightodm import generate_id

    # Update non-existent document with upsert
    # Provide _id as string to avoid ObjectId generation
    new_id = generate_id()
    success = await AsyncTestModel.aupdate_one(
        {"_id": new_id}, {"$set": {"_id": new_id, "name": "new_doc", "value": 99}}, upsert=True
    )
    assert success is True

    # Verify it was created
    result = await AsyncTestModel.afind_one({"name": "new_doc"})
    assert result is not None
    assert result.name == "new_doc"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_update_one_no_match(cleanup_test_collections):
    """Test aupdate_one returns False when no document matches."""
    success = await AsyncTestModel.aupdate_one(
        {"name": "nonexistent"}, {"$set": {"value": 999}}, upsert=False
    )
    assert success is False
