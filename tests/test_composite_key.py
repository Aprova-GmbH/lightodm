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
