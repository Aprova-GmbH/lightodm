"""Tests for synchronous CRUD operations in lightodm."""

import pytest

from lightodm import MongoBaseModel


class SyncTestModel(MongoBaseModel):
    """Test model for sync operations."""

    class Settings:
        name = "sync_test_collection"

    name: str
    value: int


@pytest.mark.integration
def test_sync_save_and_get(cleanup_test_collections):
    """Test sync save and get operations with real MongoDB."""
    # Create and save - uses real MongoDB via environment variables
    model = SyncTestModel(name="sync_test", value=42)
    doc_id = model.save()

    assert doc_id == model.id

    # Retrieve - uses real MongoDB
    retrieved = SyncTestModel.get(doc_id)
    assert retrieved is not None
    assert retrieved.name == "sync_test"
    assert retrieved.value == 42


@pytest.mark.integration
def test_sync_save_exclude_none(cleanup_test_collections):
    """Test sync save with exclude_none parameter."""

    # Add an optional field that would be None
    class ModelWithOptional(MongoBaseModel):
        class Settings:
            name = "optional_test_collection"

        name: str
        value: int
        optional: str = None

    model_opt = ModelWithOptional(name="test", value=42)
    doc_id = model_opt.save(exclude_none=True)

    # Verify it was saved
    retrieved = ModelWithOptional.get(doc_id)
    assert retrieved is not None
    assert retrieved.name == "test"


@pytest.mark.integration
def test_sync_get_nonexistent(cleanup_test_collections):
    """Test get with non-existent ID."""
    retrieved = SyncTestModel.get("507f1f77bcf86cd799439011")
    assert retrieved is None


@pytest.mark.integration
def test_sync_find(cleanup_test_collections):
    """Test sync find operations with real MongoDB."""
    # Create multiple documents
    models = [SyncTestModel(name=f"test_{i}", value=i) for i in range(5)]

    for model in models:
        model.save()

    # Find all
    results = SyncTestModel.find({})
    assert len(results) == 5

    # Find with filter
    results = SyncTestModel.find({"value": {"$gte": 3}})
    assert len(results) == 2
    assert all(r.value >= 3 for r in results)


@pytest.mark.integration
def test_sync_find_one(cleanup_test_collections):
    """Test sync find_one operation with real MongoDB."""
    # Create documents
    model1 = SyncTestModel(name="first", value=1)
    model2 = SyncTestModel(name="second", value=2)
    model1.save()
    model2.save()

    # Find one by filter
    result = SyncTestModel.find_one({"name": "second"})
    assert result is not None
    assert result.name == "second"
    assert result.value == 2

    # Find one non-existent
    result = SyncTestModel.find_one({"name": "nonexistent"})
    assert result is None


@pytest.mark.integration
def test_sync_find_iter(cleanup_test_collections):
    """Test sync find_iter operation with real MongoDB."""
    # Create documents
    models = [SyncTestModel(name=f"iter_{i}", value=i) for i in range(3)]
    for model in models:
        model.save()

    # Use iterator
    results = list(SyncTestModel.find_iter({}))
    assert len(results) == 3
    assert all(isinstance(r, SyncTestModel) for r in results)


@pytest.mark.integration
def test_sync_delete(cleanup_test_collections):
    """Test sync delete operation with real MongoDB."""
    # Create and save
    model = SyncTestModel(name="to_delete", value=100)
    model.save()

    # Verify it exists
    retrieved = SyncTestModel.get(model.id)
    assert retrieved is not None

    # Delete
    deleted = model.delete()
    assert deleted is True

    # Verify it's gone
    retrieved = SyncTestModel.get(model.id)
    assert retrieved is None


@pytest.mark.integration
def test_sync_delete_without_id(cleanup_test_collections):
    """Test delete returns False when ID is not set."""
    model = SyncTestModel(name="test", value=1)
    model.id = None
    assert model.delete() is False


@pytest.mark.integration
def test_sync_count(cleanup_test_collections):
    """Test sync count operation with real MongoDB."""
    # Create documents
    for i in range(3):
        model = SyncTestModel(name=f"count_test_{i}", value=i)
        model.save()

    # Count all
    count = SyncTestModel.count()
    assert count == 3

    # Count with filter
    count = SyncTestModel.count({"value": {"$gt": 0}})
    assert count == 2


@pytest.mark.integration
def test_sync_update_one(cleanup_test_collections):
    """Test sync update_one operation with real MongoDB."""
    # Create initial document
    model = SyncTestModel(name="original", value=10)
    model.save()

    # Update
    success = SyncTestModel.update_one({"_id": model.id}, {"$set": {"value": 20}})
    assert success is True

    # Verify update
    retrieved = SyncTestModel.get(model.id)
    assert retrieved.value == 20


@pytest.mark.integration
def test_sync_update_one_upsert(cleanup_test_collections):
    """Test sync update_one with upsert."""
    from lightodm import generate_id

    # Update non-existent document with upsert
    # Provide _id as string to avoid ObjectId generation
    new_id = generate_id()
    success = SyncTestModel.update_one(
        {"_id": new_id}, {"$set": {"_id": new_id, "name": "new_doc", "value": 99}}, upsert=True
    )
    assert success is True

    # Verify it was created
    result = SyncTestModel.find_one({"name": "new_doc"})
    assert result is not None
    assert result.name == "new_doc"


@pytest.mark.integration
def test_sync_update_one_no_match(cleanup_test_collections):
    """Test update_one returns False when no document matches."""
    success = SyncTestModel.update_one(
        {"name": "nonexistent"}, {"$set": {"value": 999}}, upsert=False
    )
    assert success is False


@pytest.mark.integration
def test_sync_update_many(cleanup_test_collections):
    """Test sync update_many operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = SyncTestModel(name=f"batch_{i}", value=i)
        model.save()

    # Update multiple
    modified_count = SyncTestModel.update_many(
        {"value": {"$gte": 3}}, {"$set": {"name": "updated"}}
    )
    assert modified_count == 2

    # Verify updates
    results = SyncTestModel.find({"name": "updated"})
    assert len(results) == 2


@pytest.mark.integration
def test_sync_delete_one(cleanup_test_collections):
    """Test sync delete_one operation with real MongoDB."""
    # Create documents
    model1 = SyncTestModel(name="delete_me", value=1)
    model2 = SyncTestModel(name="delete_me", value=2)
    model1.save()
    model2.save()

    # Delete one
    deleted = SyncTestModel.delete_one({"name": "delete_me"})
    assert deleted is True

    # Verify only one was deleted
    count = SyncTestModel.count({"name": "delete_me"})
    assert count == 1


@pytest.mark.integration
def test_sync_delete_one_no_match(cleanup_test_collections):
    """Test delete_one returns False when no document matches."""
    deleted = SyncTestModel.delete_one({"name": "nonexistent"})
    assert deleted is False


@pytest.mark.integration
def test_sync_delete_many(cleanup_test_collections):
    """Test sync delete_many operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = SyncTestModel(name=f"batch_delete_{i}", value=i)
        model.save()

    # Delete multiple
    deleted_count = SyncTestModel.delete_many({"value": {"$lt": 3}})
    assert deleted_count == 3

    # Verify remaining
    count = SyncTestModel.count()
    assert count == 2


@pytest.mark.integration
def test_sync_aggregate(cleanup_test_collections):
    """Test sync aggregate operation with real MongoDB."""
    # Create documents
    for i in range(5):
        model = SyncTestModel(name=f"agg_{i}", value=i)
        model.save()

    # Run aggregation
    pipeline = [{"$match": {"value": {"$gte": 2}}}, {"$count": "total"}]
    results = SyncTestModel.aggregate(pipeline)

    assert len(results) == 1
    assert results[0]["total"] == 3


@pytest.mark.integration
def test_sync_insert_many(cleanup_test_collections):
    """Test sync insert_many operation with real MongoDB."""
    # Create models
    models = [SyncTestModel(name=f"bulk_{i}", value=i) for i in range(3)]

    # Insert many
    ids = SyncTestModel.insert_many(models)

    assert len(ids) == 3
    assert all(isinstance(id, str) for id in ids)

    # Verify all were inserted
    count = SyncTestModel.count()
    assert count == 3


@pytest.mark.integration
def test_sync_insert_many_empty(cleanup_test_collections):
    """Test insert_many with empty list."""
    ids = SyncTestModel.insert_many([])
    assert ids == []
