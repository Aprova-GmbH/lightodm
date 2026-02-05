"""
Tests for composite key functionality in LightODM
"""

import hashlib
from typing import Optional

import pytest

from lightodm import MongoBaseModel, generate_composite_id


class TenantUser(MongoBaseModel):
    """Test model with composite key"""

    class Settings:
        name = "tenant_users"
        composite_key = ["tenant_id", "user_id"]

    tenant_id: str
    user_id: str
    data: Optional[str] = None


class ThreeFieldComposite(MongoBaseModel):
    """Test model with three-field composite key"""

    class Settings:
        name = "three_field_composite"
        composite_key = ["field_a", "field_b", "field_c"]

    field_a: str
    field_b: str
    field_c: str


class RegularModel(MongoBaseModel):
    """Test model without composite key"""

    class Settings:
        name = "regular_models"

    name: str
    value: int


class OptionalFieldModel(MongoBaseModel):
    """Test model with optional field in composite key"""

    class Settings:
        name = "optional_field_models"
        composite_key = ["required_field", "optional_field"]

    required_field: str
    optional_field: Optional[str] = None


# =============================================================================
# generate_composite_id() function tests
# =============================================================================


@pytest.mark.unit
def test_generate_composite_id_basic():
    """Test basic composite ID generation"""
    result = generate_composite_id(["tenant1", "user1"])
    expected = hashlib.md5(b"tenant1user1").hexdigest()
    assert result == expected
    assert len(result) == 32  # MD5 hex string length


@pytest.mark.unit
def test_generate_composite_id_single_value():
    """Test composite ID with single value"""
    result = generate_composite_id(["single"])
    expected = hashlib.md5(b"single").hexdigest()
    assert result == expected


@pytest.mark.unit
def test_generate_composite_id_numeric():
    """Test composite ID with numeric values"""
    result = generate_composite_id([123, 456])
    expected = hashlib.md5(b"123456").hexdigest()
    assert result == expected


@pytest.mark.unit
def test_generate_composite_id_unicode():
    """Test composite ID with unicode values"""
    result = generate_composite_id(["hello", "world"])
    expected = hashlib.md5(b"helloworld").hexdigest()
    assert result == expected


@pytest.mark.unit
def test_generate_composite_id_special_chars():
    """Test composite ID with special characters"""
    result = generate_composite_id(["test@email.com", "!@#$%"])
    expected = hashlib.md5(b"test@email.com!@#$%").hexdigest()
    assert result == expected


@pytest.mark.unit
def test_generate_composite_id_empty_string():
    """Test composite ID with empty string values"""
    result = generate_composite_id(["", "test"])
    expected = hashlib.md5(b"test").hexdigest()
    assert result == expected


@pytest.mark.unit
def test_generate_composite_id_order_matters():
    """Test that order of values affects the hash"""
    result1 = generate_composite_id(["a", "b"])
    result2 = generate_composite_id(["b", "a"])
    assert result1 != result2


# =============================================================================
# Model composite key tests
# =============================================================================


@pytest.mark.unit
def test_composite_key_basic():
    """Test basic composite key ID generation on model"""
    user = TenantUser(tenant_id="tenant1", user_id="user1", data="test")

    expected_id = hashlib.md5(b"tenant1user1").hexdigest()
    assert user.id == expected_id


@pytest.mark.unit
def test_composite_key_same_values_same_id():
    """Test that same values produce same ID (idempotent)"""
    user1 = TenantUser(tenant_id="tenant1", user_id="user1")
    user2 = TenantUser(tenant_id="tenant1", user_id="user1")

    assert user1.id == user2.id


@pytest.mark.unit
def test_composite_key_different_values_different_id():
    """Test that different values produce different IDs"""
    user1 = TenantUser(tenant_id="tenant1", user_id="user1")
    user2 = TenantUser(tenant_id="tenant1", user_id="user2")

    assert user1.id != user2.id


@pytest.mark.unit
def test_composite_key_order_preservation():
    """Test that field order in composite_key is preserved"""
    # Same values but would be different if order changed
    user = TenantUser(tenant_id="a", user_id="b")
    expected_id = hashlib.md5(b"ab").hexdigest()
    assert user.id == expected_id


@pytest.mark.unit
def test_composite_key_three_fields():
    """Test composite key with three fields"""
    model = ThreeFieldComposite(field_a="x", field_b="y", field_c="z")
    expected_id = hashlib.md5(b"xyz").hexdigest()
    assert model.id == expected_id


@pytest.mark.unit
def test_composite_key_overrides_explicit_id():
    """Test that composite key overrides any explicitly provided ID"""
    user = TenantUser(id="explicit-id", tenant_id="tenant1", user_id="user1")
    expected_id = hashlib.md5(b"tenant1user1").hexdigest()
    assert user.id == expected_id
    assert user.id != "explicit-id"


@pytest.mark.unit
def test_composite_key_numeric_values():
    """Test composite key with numeric-like string values"""
    user = TenantUser(tenant_id="123", user_id="456")
    expected_id = hashlib.md5(b"123456").hexdigest()
    assert user.id == expected_id


@pytest.mark.unit
def test_composite_key_empty_string_values():
    """Test composite key with empty string values"""
    user = TenantUser(tenant_id="", user_id="user1")
    expected_id = hashlib.md5(b"user1").hexdigest()
    assert user.id == expected_id


@pytest.mark.unit
def test_composite_key_special_characters():
    """Test composite key with special characters"""
    user = TenantUser(tenant_id="tenant@1", user_id="user#1")
    expected_id = hashlib.md5(b"tenant@1user#1").hexdigest()
    assert user.id == expected_id


# =============================================================================
# Error handling tests
# =============================================================================


@pytest.mark.unit
def test_composite_key_none_field_raises_error():
    """Test that None value in composite key field raises ValueError"""
    with pytest.raises(ValueError, match="is None"):
        OptionalFieldModel(required_field="test")  # optional_field defaults to None


@pytest.mark.unit
def test_composite_key_invalid_field_raises_error():
    """Test that invalid field name in composite_key raises ValueError"""

    class InvalidFieldModel(MongoBaseModel):
        class Settings:
            name = "invalid_field_models"
            composite_key = ["nonexistent_field"]

        actual_field: str

    with pytest.raises(ValueError, match="not found in model"):
        InvalidFieldModel(actual_field="test")


@pytest.mark.unit
def test_composite_key_empty_list_raises_error():
    """Test that empty composite_key list raises ValueError"""

    class EmptyCompositeModel(MongoBaseModel):
        class Settings:
            name = "empty_composite_models"
            composite_key = []

        field: str

    with pytest.raises(ValueError, match="non-empty list"):
        EmptyCompositeModel(field="test")


# =============================================================================
# Model without composite key tests
# =============================================================================


@pytest.mark.unit
def test_model_without_composite_key_uses_objectid():
    """Test that models without composite_key still use ObjectId"""
    model = RegularModel(name="test", value=42)

    assert model.id is not None
    assert len(model.id) == 24  # ObjectId string length


@pytest.mark.unit
def test_model_without_composite_key_generates_unique_ids():
    """Test that models without composite_key generate unique IDs"""
    model1 = RegularModel(name="test", value=42)
    model2 = RegularModel(name="test", value=42)

    assert model1.id != model2.id


# =============================================================================
# Serialization tests
# =============================================================================


@pytest.mark.unit
def test_composite_key_to_mongo_dict():
    """Test that _to_mongo_dict() works correctly with composite key"""
    user = TenantUser(tenant_id="tenant1", user_id="user1", data="test")
    data = user._to_mongo_dict()

    expected_id = hashlib.md5(b"tenant1user1").hexdigest()
    assert data["_id"] == expected_id
    assert data["tenant_id"] == "tenant1"
    assert data["user_id"] == "user1"
    assert data["data"] == "test"


@pytest.mark.unit
def test_composite_key_from_mongo_dict():
    """Test that _from_mongo_dict() works correctly with composite key"""
    expected_id = hashlib.md5(b"tenant1user1").hexdigest()
    doc = {
        "_id": expected_id,
        "tenant_id": "tenant1",
        "user_id": "user1",
        "data": "test",
    }

    user = TenantUser._from_mongo_dict(doc)

    # When loading from MongoDB, the ID should be preserved (not recomputed)
    # since the model_validator runs but the ID is already set
    assert user.tenant_id == "tenant1"
    assert user.user_id == "user1"
    assert user.data == "test"
    # The composite key will recompute the ID, which should match
    assert user.id == expected_id


@pytest.mark.unit
def test_composite_key_roundtrip():
    """Test full roundtrip: create -> to_mongo_dict -> from_mongo_dict"""
    original = TenantUser(tenant_id="tenant1", user_id="user1", data="test")
    mongo_data = original._to_mongo_dict()
    loaded = TenantUser._from_mongo_dict(mongo_data)

    assert loaded.id == original.id
    assert loaded.tenant_id == original.tenant_id
    assert loaded.user_id == original.user_id
    assert loaded.data == original.data


# =============================================================================
# Integration tests (require MongoDB)
# =============================================================================


@pytest.mark.integration
def test_composite_key_save_and_get(cleanup_test_collections):
    """Test saving and retrieving a model with composite key."""
    user = TenantUser(tenant_id="tenant1", user_id="user1", data="test_data")
    doc_id = user.save()

    # ID should be the composite key hash
    expected_id = hashlib.md5(b"tenant1user1").hexdigest()
    assert doc_id == expected_id

    # Retrieve by ID
    retrieved = TenantUser.get(doc_id)
    assert retrieved is not None
    assert retrieved.tenant_id == "tenant1"
    assert retrieved.user_id == "user1"
    assert retrieved.data == "test_data"
    assert retrieved.id == expected_id


@pytest.mark.integration
def test_composite_key_upsert_behavior(cleanup_test_collections):
    """Test that saving same composite key updates existing document."""
    # Create initial document
    user1 = TenantUser(tenant_id="tenant1", user_id="user1", data="original")
    user1.save()

    # Create another instance with same composite key but different data
    user2 = TenantUser(tenant_id="tenant1", user_id="user1", data="updated")
    user2.save()

    # Both should have the same ID
    assert user1.id == user2.id

    # Should only be one document in the collection
    count = TenantUser.count({})
    assert count == 1

    # The document should have the updated data
    retrieved = TenantUser.get(user1.id)
    assert retrieved.data == "updated"


@pytest.mark.integration
def test_composite_key_find_by_fields(cleanup_test_collections):
    """Test finding documents by composite key fields."""
    # Create multiple documents
    TenantUser(tenant_id="tenant1", user_id="user1", data="data1").save()
    TenantUser(tenant_id="tenant1", user_id="user2", data="data2").save()
    TenantUser(tenant_id="tenant2", user_id="user1", data="data3").save()

    # Find by tenant_id
    results = TenantUser.find({"tenant_id": "tenant1"})
    assert len(results) == 2

    # Find by both fields
    result = TenantUser.find_one({"tenant_id": "tenant1", "user_id": "user2"})
    assert result is not None
    assert result.data == "data2"


@pytest.mark.integration
def test_composite_key_delete(cleanup_test_collections):
    """Test deleting a document with composite key."""
    user = TenantUser(tenant_id="tenant1", user_id="user1", data="to_delete")
    user.save()

    # Verify it exists
    assert TenantUser.get(user.id) is not None

    # Delete
    deleted = user.delete()
    assert deleted is True

    # Verify it's gone
    assert TenantUser.get(user.id) is None


@pytest.mark.integration
def test_composite_key_insert_many(cleanup_test_collections):
    """Test bulk inserting documents with composite keys."""
    users = [TenantUser(tenant_id="tenant1", user_id=f"user{i}", data=f"data{i}") for i in range(3)]

    ids = TenantUser.insert_many(users)
    assert len(ids) == 3

    # Each ID should be deterministic
    for i, _user in enumerate(users):
        expected_id = hashlib.md5(f"tenant1user{i}".encode()).hexdigest()
        assert ids[i] == expected_id


@pytest.mark.integration
async def test_composite_key_async_save_and_get(cleanup_test_collections):
    """Test async save and get with composite key."""
    user = TenantUser(tenant_id="tenant_async", user_id="user_async", data="async_data")
    doc_id = await user.asave()

    expected_id = hashlib.md5(b"tenant_asyncuser_async").hexdigest()
    assert doc_id == expected_id

    # Retrieve
    retrieved = await TenantUser.aget(doc_id)
    assert retrieved is not None
    assert retrieved.tenant_id == "tenant_async"
    assert retrieved.user_id == "user_async"
    assert retrieved.data == "async_data"


@pytest.mark.integration
async def test_composite_key_async_upsert(cleanup_test_collections):
    """Test async upsert behavior with composite key."""
    # Create initial
    user1 = TenantUser(tenant_id="tenant_async", user_id="user1", data="original")
    await user1.asave()

    # Update with same composite key
    user2 = TenantUser(tenant_id="tenant_async", user_id="user1", data="updated_async")
    await user2.asave()

    # Should be only one document
    count = await TenantUser.acount({})
    assert count == 1

    # Should have updated data
    retrieved = await TenantUser.aget(user1.id)
    assert retrieved.data == "updated_async"


@pytest.mark.integration
async def test_composite_key_async_find(cleanup_test_collections):
    """Test async find with composite key models."""
    # Create documents
    await TenantUser(tenant_id="t1", user_id="u1", data="d1").asave()
    await TenantUser(tenant_id="t1", user_id="u2", data="d2").asave()
    await TenantUser(tenant_id="t2", user_id="u1", data="d3").asave()

    # Find
    results = await TenantUser.afind({"tenant_id": "t1"})
    assert len(results) == 2

    # Find one
    result = await TenantUser.afind_one({"tenant_id": "t2"})
    assert result is not None
    assert result.data == "d3"


@pytest.mark.integration
async def test_composite_key_async_delete(cleanup_test_collections):
    """Test async delete with composite key."""
    user = TenantUser(tenant_id="t_del", user_id="u_del", data="delete_me")
    await user.asave()

    # Verify exists
    assert await TenantUser.aget(user.id) is not None

    # Delete
    deleted = await user.adelete()
    assert deleted is True

    # Verify gone
    assert await TenantUser.aget(user.id) is None
