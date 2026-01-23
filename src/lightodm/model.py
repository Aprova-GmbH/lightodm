"""
MongoDB Base Model for Pydantic

Provides ODM functionality for MongoDB with both sync and async support.
"""

from typing import AsyncIterator, Iterator, List, Optional, Type, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, ConfigDict, Field
from pymongo.collection import Collection as PyMongoCollection

from lightodm.connection import get_async_database, get_collection

# TypeVar for generic class methods
T = TypeVar("T", bound="MongoBaseModel")


def generate_id() -> str:
    """
    Generate a new MongoDB ObjectId as a string.

    Returns:
        String representation of a new ObjectId
    """
    return str(ObjectId())


class MongoBaseModel(BaseModel):
    """
    Base class for MongoDB document models with ODM functionality.

    Provides both synchronous and asynchronous methods for CRUD operations.
    Maps Pydantic 'id' field to MongoDB '_id' field.

    Subclasses must define an inner Settings class with 'name' attribute:

    Example:
        class User(MongoBaseModel):
            class Settings:
                name = "users"

            name: str
            email: str
            age: Optional[int] = None

        # Sync usage
        user = User(name="John", email="john@example.com")
        user.save()

        found_user = User.get("some_id")
        users = User.find({"age": {"$gt": 18}})

        # Async usage
        await user.asave()
        found_user = await User.aget("some_id")
        users = await User.afind({"age": {"$gt": 18}})
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # ID field that maps to MongoDB _id
    id: Optional[str] = Field(default_factory=generate_id, alias="_id")

    # Settings inner class - must be overridden in subclasses
    class Settings:
        name: Optional[str] = None  # MongoDB collection name

    @classmethod
    def _uses_mongo_id_alias(cls) -> bool:
        field = cls.model_fields.get("id")
        if field is None:
            return False
        alias = getattr(field, "serialization_alias", None) or getattr(field, "alias", None)
        if alias is None:
            alias = getattr(field, "validation_alias", None)
        return alias == "_id"

    def __init_subclass__(cls, **kwargs):
        """
        Validate Settings class is properly defined in subclass.
        """
        super().__init_subclass__(**kwargs)
        # Skip validation for the base class itself
        if cls.__name__ == "MongoBaseModel":
            return

        # Check if Settings class exists and has name attribute
        if not hasattr(cls, "Settings"):
            # Allow intermediate base classes without Settings
            pass
        elif hasattr(cls.Settings, "name") and cls.Settings.name is None:
            # Settings exists but name is None - could be intermediate class
            pass

    @classmethod
    def _validate_collection_name(cls):
        """Ensure Settings.name is defined in subclass"""
        if not hasattr(cls, "Settings"):
            raise NotImplementedError(f"{cls.__name__} must define an inner 'Settings' class")
        if not hasattr(cls.Settings, "name") or cls.Settings.name is None:
            raise NotImplementedError(
                f"{cls.__name__}.Settings must define 'name' attribute with the collection name"
            )

    @classmethod
    def _get_collection_name(cls) -> str:
        """Get the collection name from Settings.name"""
        cls._validate_collection_name()
        return cls.Settings.name

    @classmethod
    def get_collection(cls) -> PyMongoCollection:
        """
        Get synchronous MongoDB collection.

        Override this method to provide custom connection logic.

        Returns:
            PyMongo Collection instance
        """
        collection_name = cls._get_collection_name()
        return get_collection(collection_name)

    @classmethod
    async def get_async_collection(cls) -> AsyncIOMotorCollection:
        """
        Get asynchronous MongoDB collection.

        Override this method to provide custom connection logic.

        Returns:
            Motor AsyncIOMotorCollection instance
        """
        collection_name = cls._get_collection_name()
        db = await get_async_database()
        return db[collection_name]

    def _to_mongo_dict(self, exclude_none: bool = False) -> dict:
        """
        Convert model to dictionary for MongoDB, handling id -> _id mapping.

        Only serializes Pydantic fields - class attributes like collection_name
        are automatically excluded.

        Args:
            exclude_none: If True, exclude fields with None values

        Returns:
            Dictionary suitable for MongoDB insertion/update
        """
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        if not self._uses_mongo_id_alias():
            if "id" in data and "_id" not in data:
                data["_id"] = data.pop("id")
            else:
                data.pop("id", None)
        # Manually add extra fields that were captured
        extra_fields = self.__pydantic_extra__
        if extra_fields:
            for key, value in extra_fields.items():
                if not exclude_none or value is not None:
                    data[key] = value
        return data

    @classmethod
    def _from_mongo_dict(cls: Type[T], data: dict) -> Optional[T]:
        """
        Create model instance from MongoDB document.

        Args:
            data: MongoDB document dictionary

        Returns:
            Model instance or None if data is None
        """
        if data is None:
            return None
        if not cls._uses_mongo_id_alias() and "_id" in data and "id" not in data:
            data = dict(data)
            data["id"] = data["_id"]

        return cls.model_validate(data)

    # ==================== CRUD Operations (Sync) ====================

    @classmethod
    def get(cls: Type[T], id: str) -> Optional[T]:
        """
        Retrieve a document by ID (synchronous).

        Args:
            id: Document ID

        Returns:
            Model instance or None if not found
        """
        collection = cls.get_collection()
        doc = collection.find_one({"_id": id})
        return cls._from_mongo_dict(doc)

    def save(self, exclude_none: bool = False) -> str:
        """
        Save/upsert the document (synchronous).

        Args:
            exclude_none: If True, exclude fields with None values from update

        Returns:
            Document ID
        """
        collection = self.get_collection()
        data = self._to_mongo_dict(exclude_none=exclude_none)
        doc_id = data.get("_id")
        if doc_id is None:
            raise ValueError("Document ID is required")

        collection.replace_one({"_id": doc_id}, data, upsert=True)
        return doc_id

    def delete(self) -> bool:
        """
        Delete the document (synchronous).

        Returns:
            True if document was deleted, False otherwise
        """
        if not self.id:
            return False

        collection = self.get_collection()
        result = collection.delete_one({"_id": self.id})
        return result.deleted_count > 0

    @classmethod
    def find_one(cls: Type[T], filter: dict, **kwargs) -> Optional[T]:
        """
        Find a single document (synchronous).

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find_one (e.g., sort, projection)

        Returns:
            Model instance or None if not found
        """
        collection = cls.get_collection()
        doc = collection.find_one(filter, **kwargs)
        return cls._from_mongo_dict(doc)

    @classmethod
    def find(cls: Type[T], filter: dict, **kwargs) -> List[T]:
        """
        Find multiple documents (synchronous).

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find (e.g., sort, limit, skip, projection)

        Returns:
            List of model instances
        """
        collection = cls.get_collection()
        cursor = collection.find(filter, **kwargs)
        return [cls._from_mongo_dict(doc) for doc in cursor]

    @classmethod
    def find_iter(cls: Type[T], filter: dict, **kwargs) -> Iterator[T]:
        """
        Find multiple documents with iterator (synchronous).
        Useful for large result sets to avoid loading all into memory.

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find

        Yields:
            Model instances one at a time
        """
        collection = cls.get_collection()
        cursor = collection.find(filter, **kwargs)
        for doc in cursor:
            yield cls._from_mongo_dict(doc)

    @classmethod
    def count(cls, filter: dict = None) -> int:
        """
        Count documents matching filter (synchronous).

        Args:
            filter: MongoDB filter dictionary (default: {} for all documents)

        Returns:
            Number of matching documents
        """
        collection = cls.get_collection()
        return collection.count_documents(filter or {})

    @classmethod
    def update_one(cls, filter: dict, update: dict, upsert: bool = False) -> bool:
        """
        Update a single document (synchronous).

        Args:
            filter: MongoDB filter dictionary
            update: MongoDB update dictionary (should include operators like $set)
            upsert: If True, insert document if not found

        Returns:
            True if document was modified, False otherwise
        """
        collection = cls.get_collection()
        result = collection.update_one(filter, update, upsert=upsert)
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)

    @classmethod
    def update_many(cls, filter: dict, update: dict) -> int:
        """
        Update multiple documents (synchronous).

        Args:
            filter: MongoDB filter dictionary
            update: MongoDB update dictionary (should include operators like $set)

        Returns:
            Number of documents modified
        """
        collection = cls.get_collection()
        result = collection.update_many(filter, update)
        return result.modified_count

    @classmethod
    def delete_one(cls, filter: dict) -> bool:
        """
        Delete a single document (synchronous).

        Args:
            filter: MongoDB filter dictionary

        Returns:
            True if document was deleted, False otherwise
        """
        collection = cls.get_collection()
        result = collection.delete_one(filter)
        return result.deleted_count > 0

    @classmethod
    def delete_many(cls, filter: dict) -> int:
        """
        Delete multiple documents (synchronous).

        Args:
            filter: MongoDB filter dictionary

        Returns:
            Number of documents deleted
        """
        collection = cls.get_collection()
        result = collection.delete_many(filter)
        return result.deleted_count

    # ==================== CRUD Operations (Async) ====================

    @classmethod
    async def aget(cls: Type[T], id: str) -> Optional[T]:
        """
        Retrieve a document by ID (asynchronous).

        Args:
            id: Document ID

        Returns:
            Model instance or None if not found
        """
        collection = await cls.get_async_collection()
        doc = await collection.find_one({"_id": id})
        return cls._from_mongo_dict(doc)

    async def asave(self, exclude_none: bool = False) -> str:
        """
        Save/upsert the document (asynchronous).

        Args:
            exclude_none: If True, exclude fields with None values from update

        Returns:
            Document ID
        """
        collection = await self.get_async_collection()
        data = self._to_mongo_dict(exclude_none=exclude_none)
        doc_id = data.get("_id")
        if doc_id is None:
            raise ValueError("Document ID is required")

        await collection.replace_one({"_id": doc_id}, data, upsert=True)
        return doc_id

    async def adelete(self) -> bool:
        """
        Delete the document (asynchronous).

        Returns:
            True if document was deleted, False otherwise
        """
        if not self.id:
            return False

        collection = await self.get_async_collection()
        result = await collection.delete_one({"_id": self.id})
        return result.deleted_count > 0

    @classmethod
    async def afind_one(cls: Type[T], filter: dict, **kwargs) -> Optional[T]:
        """
        Find a single document (asynchronous).

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find_one (e.g., sort, projection)

        Returns:
            Model instance or None if not found
        """
        collection = await cls.get_async_collection()
        doc = await collection.find_one(filter, **kwargs)
        return cls._from_mongo_dict(doc)

    @classmethod
    async def afind(cls: Type[T], filter: dict, **kwargs) -> List[T]:
        """
        Find multiple documents (asynchronous).

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find (e.g., sort, limit, skip, projection)

        Returns:
            List of model instances
        """
        collection = await cls.get_async_collection()
        cursor = collection.find(filter, **kwargs)
        docs = await cursor.to_list(length=None)
        return [cls._from_mongo_dict(doc) for doc in docs]

    @classmethod
    async def afind_iter(cls: Type[T], filter: dict, **kwargs) -> AsyncIterator[T]:
        """
        Find multiple documents with async iterator.
        Useful for large result sets to avoid loading all into memory.

        Args:
            filter: MongoDB filter dictionary
            **kwargs: Additional arguments passed to find

        Yields:
            Model instances one at a time
        """
        collection = await cls.get_async_collection()
        cursor = collection.find(filter, **kwargs)
        async for doc in cursor:
            yield cls._from_mongo_dict(doc)

    @classmethod
    async def acount(cls, filter: dict = None) -> int:
        """
        Count documents matching filter (asynchronous).

        Args:
            filter: MongoDB filter dictionary (default: {} for all documents)

        Returns:
            Number of matching documents
        """
        collection = await cls.get_async_collection()
        return await collection.count_documents(filter or {})

    @classmethod
    async def aupdate_one(cls, filter: dict, update: dict, upsert: bool = False) -> bool:
        """
        Update a single document (asynchronous).

        Args:
            filter: MongoDB filter dictionary
            update: MongoDB update dictionary (should include operators like $set)
            upsert: If True, insert document if not found

        Returns:
            True if document was modified, False otherwise
        """
        collection = await cls.get_async_collection()
        result = await collection.update_one(filter, update, upsert=upsert)
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)

    @classmethod
    async def aupdate_many(cls, filter: dict, update: dict) -> int:
        """
        Update multiple documents (asynchronous).

        Args:
            filter: MongoDB filter dictionary
            update: MongoDB update dictionary (should include operators like $set)

        Returns:
            Number of documents modified
        """
        collection = await cls.get_async_collection()
        result = await collection.update_many(filter, update)
        return result.modified_count

    @classmethod
    async def adelete_one(cls, filter: dict) -> bool:
        """
        Delete a single document (asynchronous).

        Args:
            filter: MongoDB filter dictionary

        Returns:
            True if document was deleted, False otherwise
        """
        collection = await cls.get_async_collection()
        result = await collection.delete_one(filter)
        return result.deleted_count > 0

    @classmethod
    async def adelete_many(cls, filter: dict) -> int:
        """
        Delete multiple documents (asynchronous).

        Args:
            filter: MongoDB filter dictionary

        Returns:
            Number of documents deleted
        """
        collection = await cls.get_async_collection()
        result = await collection.delete_many(filter)
        return result.deleted_count

    # ==================== Aggregation Operations ====================

    @classmethod
    def aggregate(cls: Type[T], pipeline: List[dict], **kwargs) -> List[dict]:
        """
        Run aggregation pipeline (synchronous).

        Args:
            pipeline: MongoDB aggregation pipeline
            **kwargs: Additional arguments passed to aggregate

        Returns:
            List of result documents
        """
        collection = cls.get_collection()
        cursor = collection.aggregate(pipeline, **kwargs)
        return list(cursor)

    @classmethod
    async def aaggregate(cls: Type[T], pipeline: List[dict], **kwargs) -> List[dict]:
        """
        Run aggregation pipeline (asynchronous).

        Args:
            pipeline: MongoDB aggregation pipeline
            **kwargs: Additional arguments passed to aggregate

        Returns:
            List of result documents
        """
        collection = await cls.get_async_collection()
        cursor = collection.aggregate(pipeline, **kwargs)
        return await cursor.to_list(length=None)

    # ==================== Bulk Operations ====================

    @classmethod
    def insert_many(cls: Type[T], documents: List[T]) -> List[str]:
        """
        Insert multiple documents (synchronous).

        Args:
            documents: List of model instances

        Returns:
            List of inserted document IDs
        """
        if not documents:
            return []

        collection = cls.get_collection()
        docs = [doc._to_mongo_dict() for doc in documents]
        result = collection.insert_many(docs)
        return [str(id) for id in result.inserted_ids]

    @classmethod
    async def ainsert_many(cls: Type[T], documents: List[T]) -> List[str]:
        """
        Insert multiple documents (asynchronous).

        Args:
            documents: List of model instances

        Returns:
            List of inserted document IDs
        """
        if not documents:
            return []

        collection = await cls.get_async_collection()
        docs = [doc._to_mongo_dict() for doc in documents]
        result = await collection.insert_many(docs)
        return [str(id) for id in result.inserted_ids]
