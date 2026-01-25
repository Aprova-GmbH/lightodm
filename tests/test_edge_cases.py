"""Edge case tests for LightODM."""

import pytest
from pydantic import Field

from lightodm import MongoBaseModel, generate_id


class EdgeCaseModel(MongoBaseModel):
    """Test model for edge cases."""

    class Settings:
        name = "edge_case_collection"

    name: str
    value: int


class CustomIdModel(MongoBaseModel):
    """Model with custom ID using alias."""

    class Settings:
        name = "custom_id_collection"

    id: str = Field(default_factory=generate_id, alias="_id")
    name: str


@pytest.mark.unit
def test_uses_mongo_id_alias_with_alias():
    """Test _uses_mongo_id_alias when id field has _id alias."""
    assert CustomIdModel._uses_mongo_id_alias() is True


@pytest.mark.unit
def test_uses_mongo_id_alias_without_alias():
    """Test _uses_mongo_id_alias - all models inherit _id alias from base."""
    # All models inherit the id field with _id alias from MongoBaseModel
    assert EdgeCaseModel._uses_mongo_id_alias() is True


@pytest.mark.unit
def test_uses_mongo_id_alias_no_id_field():
    """Test _uses_mongo_id_alias when model has no id field."""
    # Even if we don't explicitly define id, it's inherited from MongoBaseModel
    # So all models will have the _id alias
    class NoIdModel(MongoBaseModel):
        class Settings:
            name = "no_id_collection"

        name: str

    # Model inherits id field with _id alias from base class
    assert NoIdModel._uses_mongo_id_alias() is True


@pytest.mark.unit
def test_subclass_without_settings():
    """Test that subclass without Settings can be created."""

    # This is an intermediate base class - should not raise error
    class IntermediateBase(MongoBaseModel):
        common_field: str

    # Should be able to instantiate
    instance = IntermediateBase(common_field="test")
    assert instance.common_field == "test"


@pytest.mark.unit
def test_subclass_with_none_collection_name():
    """Test that subclass with Settings.name = None can be created."""

    class IntermediateBase(MongoBaseModel):
        class Settings:
            name = None

        common_field: str

    # Should be able to instantiate
    instance = IntermediateBase(common_field="test")
    assert instance.common_field == "test"


@pytest.mark.integration
def test_sync_save_without_id_raises_error(cleanup_test_collections):
    """Test that save raises error when document ID is None."""
    model = EdgeCaseModel(name="test", value=1)
    # Force id to be None
    model.id = None

    with pytest.raises(ValueError, match="Document ID is required"):
        model.save()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_save_without_id_raises_error(cleanup_test_collections):
    """Test that asave raises error when document ID is None."""
    model = EdgeCaseModel(name="test", value=1)
    # Force id to be None
    model.id = None

    with pytest.raises(ValueError, match="Document ID is required"):
        await model.asave()


@pytest.mark.integration
def test_custom_id_field_with_alias(cleanup_test_collections):
    """Test model with custom ID field using _id alias."""
    # Create model with custom ID
    model = CustomIdModel(id="custom-123", name="Custom")
    model.save()

    # Retrieve and verify
    retrieved = CustomIdModel.get("custom-123")
    assert retrieved is not None
    assert retrieved.id == "custom-123"
    assert retrieved.name == "Custom"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_custom_id_field_with_alias(cleanup_test_collections):
    """Test async operations with model using custom ID field."""
    # Create model with custom ID
    model = CustomIdModel(id="async-custom-123", name="AsyncCustom")
    await model.asave()

    # Retrieve and verify
    retrieved = await CustomIdModel.aget("async-custom-123")
    assert retrieved is not None
    assert retrieved.id == "async-custom-123"
    assert retrieved.name == "AsyncCustom"


@pytest.mark.integration
def test_find_with_kwargs(cleanup_test_collections):
    """Test find with additional kwargs like limit and sort."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"test_{i}", value=i)
        model.save()

    # Find with limit
    results = EdgeCaseModel.find({}, limit=2)
    assert len(results) == 2

    # Find with sort
    results = EdgeCaseModel.find({}, sort=[("value", -1)], limit=3)
    assert len(results) == 3
    assert results[0].value > results[1].value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find_with_kwargs(cleanup_test_collections):
    """Test async find with additional kwargs like limit and sort."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"test_{i}", value=i)
        await model.asave()

    # Find with limit
    results = await EdgeCaseModel.afind({}, limit=2)
    assert len(results) == 2

    # Find with sort
    results = await EdgeCaseModel.afind({}, sort=[("value", -1)], limit=3)
    assert len(results) == 3
    assert results[0].value > results[1].value


@pytest.mark.integration
def test_find_one_with_kwargs(cleanup_test_collections):
    """Test find_one with kwargs like sort."""
    # Create documents
    for i in range(3):
        model = EdgeCaseModel(name="test", value=i)
        model.save()

    # Find one with sort
    result = EdgeCaseModel.find_one({"name": "test"}, sort=[("value", -1)])
    assert result is not None
    assert result.value == 2  # Highest value due to descending sort


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find_one_with_kwargs(cleanup_test_collections):
    """Test async find_one with kwargs like sort."""
    # Create documents
    for i in range(3):
        model = EdgeCaseModel(name="test", value=i)
        await model.asave()

    # Find one with sort
    result = await EdgeCaseModel.afind_one({"name": "test"}, sort=[("value", -1)])
    assert result is not None
    assert result.value == 2  # Highest value due to descending sort


@pytest.mark.integration
def test_aggregate_with_kwargs(cleanup_test_collections):
    """Test aggregate with additional kwargs."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"agg_{i}", value=i)
        model.save()

    # Run aggregation with allowDiskUse
    pipeline = [{"$match": {"value": {"$gte": 2}}}, {"$sort": {"value": -1}}]
    results = EdgeCaseModel.aggregate(pipeline, allowDiskUse=True)

    assert len(results) == 3
    assert results[0]["value"] == 4  # Sorted descending


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_aggregate_with_kwargs(cleanup_test_collections):
    """Test async aggregate with additional kwargs."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"agg_{i}", value=i)
        await model.asave()

    # Run aggregation
    pipeline = [{"$match": {"value": {"$gte": 2}}}, {"$sort": {"value": -1}}]
    results = await EdgeCaseModel.aaggregate(pipeline)

    assert len(results) == 3
    assert results[0]["value"] == 4  # Sorted descending


@pytest.mark.integration
def test_find_iter_with_kwargs(cleanup_test_collections):
    """Test find_iter with kwargs like limit."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"iter_{i}", value=i)
        model.save()

    # Use iterator with limit
    results = list(EdgeCaseModel.find_iter({}, limit=2))
    assert len(results) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_find_iter_with_kwargs(cleanup_test_collections):
    """Test async find_iter with kwargs like limit."""
    # Create documents
    for i in range(5):
        model = EdgeCaseModel(name=f"iter_{i}", value=i)
        await model.asave()

    # Use async iterator with limit
    results = []
    async for doc in EdgeCaseModel.afind_iter({}, limit=2):
        results.append(doc)
    assert len(results) == 2
