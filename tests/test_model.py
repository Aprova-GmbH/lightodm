"""
Basic tests for LightODM model functionality
"""

import pytest
from typing import Optional
from lightodm import MongoBaseModel, generate_id


class TestUser(MongoBaseModel):
    """Test model for unit tests"""

    class Settings:
        name = "test_users"

    name: str
    email: str
    age: Optional[int] = None


def test_generate_id():
    """Test ID generation"""
    id1 = generate_id()
    id2 = generate_id()

    assert id1 != id2
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert len(id1) == 24  # ObjectId string length


def test_model_creation():
    """Test model instantiation"""
    user = TestUser(name="John Doe", email="john@example.com", age=30)

    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.age == 30
    assert user.id is not None
    assert isinstance(user.id, str)


def test_model_default_id():
    """Test that ID is auto-generated"""
    user1 = TestUser(name="User 1", email="user1@example.com")
    user2 = TestUser(name="User 2", email="user2@example.com")

    assert user1.id is not None
    assert user2.id is not None
    assert user1.id != user2.id


def test_to_mongo_dict():
    """Test conversion to MongoDB dictionary"""
    user = TestUser(name="John Doe", email="john@example.com", age=30)
    data = user._to_mongo_dict()

    assert "_id" in data
    assert data["_id"] == user.id
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["age"] == 30


def test_to_mongo_dict_exclude_none():
    """Test conversion with exclude_none"""
    user = TestUser(name="John Doe", email="john@example.com")
    data = user._to_mongo_dict(exclude_none=True)

    assert "_id" in data
    assert "name" in data
    assert "email" in data
    assert "age" not in data  # None value excluded


def test_from_mongo_dict():
    """Test creation from MongoDB document"""
    doc = {
        "_id": "507f1f77bcf86cd799439011",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }

    user = TestUser._from_mongo_dict(doc)

    assert user.id == "507f1f77bcf86cd799439011"
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.age == 30


def test_from_mongo_dict_none():
    """Test _from_mongo_dict with None input"""
    user = TestUser._from_mongo_dict(None)
    assert user is None


def test_extra_fields():
    """Test that extra fields are allowed"""
    user = TestUser(
        name="John Doe",
        email="john@example.com",
        custom_field="custom_value"
    )

    # Extra fields should be stored
    assert hasattr(user, '__pydantic_extra__')

    # Should be included in mongo dict
    data = user._to_mongo_dict()
    assert data.get("custom_field") == "custom_value"


def test_collection_name_validation():
    """Test that Settings.name is validated"""

    # This should work
    class ValidModel(MongoBaseModel):
        class Settings:
            name = "valid_collection"

        field: str

    # Getting collection name should work
    assert ValidModel._get_collection_name() == "valid_collection"

    # This should raise error when trying to get collection
    class InvalidModel(MongoBaseModel):
        field: str

    with pytest.raises(NotImplementedError):
        InvalidModel._get_collection_name()
