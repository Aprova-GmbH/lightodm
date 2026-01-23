"""
LightODM - Lightweight MongoDB ODM

A simple, lightweight Object-Document Mapper (ODM) for MongoDB with full async/sync support.
Alternative to Beanie with zero dependencies beyond Pydantic, PyMongo, and Motor.

Example:
    from lightodm import MongoBaseModel

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str
        age: int = None

    # Sync usage
    user = User(name="John", email="john@example.com")
    user.save()

    # Async usage
    await user.asave()
"""

__version__ = "0.1.0"

from lightodm.connection import (
    MongoConnection,
    connect,
    get_async_client,
    get_async_database,
    get_client,
    get_collection,
    get_database,
    get_mongo_connection,
)
from lightodm.model import MongoBaseModel, generate_id

__all__ = [
    # Model
    "MongoBaseModel",
    "generate_id",
    # Connection
    "MongoConnection",
    "connect",
    "get_mongo_connection",
    "get_collection",
    "get_async_database",
    "get_database",
    "get_client",
    "get_async_client",
]
