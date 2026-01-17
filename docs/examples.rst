Usage Examples
==============

This page demonstrates real-world usage patterns for LightODM.

FastAPI Integration
-------------------

Complete example of using LightODM with FastAPI for a REST API:

.. code-block:: python

    from fastapi import FastAPI, HTTPException
    from lightodm import connect, MongoBaseModel
    from typing import Optional, List
    from pydantic import EmailStr

    # Initialize connection on startup
    app = FastAPI()

    @app.on_event("startup")
    async def startup():
        connect(db_name="myapp")

    # Define model
    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: EmailStr
        age: Optional[int] = None

    # Create user endpoint
    @app.post("/users/", response_model=User)
    async def create_user(user: User):
        await user.asave()
        return user

    # Get user endpoint
    @app.get("/users/{user_id}", response_model=User)
    async def get_user(user_id: str):
        user = await User.aget(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    # List users endpoint
    @app.get("/users/", response_model=List[User])
    async def list_users(skip: int = 0, limit: int = 10):
        users = await User.afind({}, skip=skip, limit=limit)
        return users

    # Update user endpoint
    @app.put("/users/{user_id}", response_model=User)
    async def update_user(user_id: str, user: User):
        existing = await User.aget(user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")

        user.id = user_id
        await user.asave()
        return user

    # Delete user endpoint
    @app.delete("/users/{user_id}")
    async def delete_user(user_id: str):
        user = await User.aget(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await user.adelete()
        return {"message": "User deleted"}

Custom Connection Management
-----------------------------

For advanced scenarios, implement custom connection logic:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient
    import os

    # Global connection instances
    SYNC_CLIENT = None
    ASYNC_CLIENT = None
    DB_NAME = os.getenv("MONGO_DB_NAME", "myapp")

    def get_sync_client():
        global SYNC_CLIENT
        if SYNC_CLIENT is None:
            SYNC_CLIENT = MongoClient(os.getenv("MONGO_URL"))
        return SYNC_CLIENT

    async def get_async_client():
        global ASYNC_CLIENT
        if ASYNC_CLIENT is None:
            ASYNC_CLIENT = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        return ASYNC_CLIENT

    # Base model with custom connection
    class MyBaseModel(MongoBaseModel):
        @classmethod
        def get_collection(cls):
            client = get_sync_client()
            return client[DB_NAME][cls.Settings.name]

        @classmethod
        async def get_async_collection(cls):
            client = await get_async_client()
            return client[DB_NAME][cls.Settings.name]

    # Use in models
    class User(MyBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

Multi-Tenant Application
-------------------------

Implement multi-tenancy by dynamically selecting database:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient
    from contextvars import ContextVar

    # Context variable to track current tenant
    current_tenant: ContextVar[str] = ContextVar("current_tenant")

    client = MongoClient("mongodb://localhost:27017")
    async_client = AsyncIOMotorClient("mongodb://localhost:27017")

    class TenantModel(MongoBaseModel):
        """Base model for multi-tenant collections"""

        @classmethod
        def get_collection(cls):
            tenant = current_tenant.get()
            db_name = f"tenant_{tenant}"
            return client[db_name][cls.Settings.name]

        @classmethod
        async def get_async_collection(cls):
            tenant = current_tenant.get()
            db_name = f"tenant_{tenant}"
            return async_client[db_name][cls.Settings.name]

    class User(TenantModel):
        class Settings:
            name = "users"

        name: str
        email: str

    # Usage with FastAPI
    from fastapi import FastAPI, Header

    app = FastAPI()

    @app.get("/users/")
    async def list_users(x_tenant_id: str = Header(...)):
        # Set tenant context
        current_tenant.set(x_tenant_id)

        # Query uses tenant-specific database
        users = await User.afind({})
        return users

Custom ID Generation
--------------------

Generate custom IDs based on business logic:

.. code-block:: python

    from lightodm import MongoBaseModel, generate_id
    from pydantic import Field

    class Order(MongoBaseModel):
        class Settings:
            name = "orders"

        # Generate deterministic ID from user_id and timestamp
        id: str = Field(
            default_factory=lambda: generate_id(
                prefix="ORDER",
                timestamp=datetime.now().timestamp()
            )
        )

        user_id: str
        total: float
        items: List[str]

    # Or override __init__
    class Product(MongoBaseModel):
        class Settings:
            name = "products"

        sku: str
        name: str
        price: float

        def __init__(self, **data):
            if "id" not in data:
                # Use SKU as ID
                data["id"] = generate_id(sku=data["sku"])
            super().__init__(**data)

Bulk Operations
---------------

Efficiently process large datasets:

.. code-block:: python

    from lightodm import MongoBaseModel
    from typing import List

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

    # Bulk insert
    async def bulk_create_users(users_data: List[dict]):
        users = [User(**data) for data in users_data]
        ids = await User.ainsert_many(users)
        return ids

    # Batch processing with iteration
    async def process_all_users():
        batch_size = 100
        batch = []

        async for user in User.afind_iter({}):
            batch.append(user)

            if len(batch) >= batch_size:
                # Process batch
                await process_batch(batch)
                batch = []

        # Process remaining
        if batch:
            await process_batch(batch)

    async def process_batch(users: List[User]):
        # Process users in batch
        for user in users:
            # Do something
            pass

Aggregation Pipeline
--------------------

Complex analytics with MongoDB aggregation:

.. code-block:: python

    from lightodm import MongoBaseModel
    from datetime import datetime, timedelta

    class Order(MongoBaseModel):
        class Settings:
            name = "orders"

        user_id: str
        total: float
        created_at: datetime
        status: str

    # Revenue by date
    async def get_daily_revenue(start_date: datetime, end_date: datetime):
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "revenue": {"$sum": "$total"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        results = await Order.aaggregate(pipeline)
        return results

    # Top customers
    async def get_top_customers(limit: int = 10):
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "total_spent": {"$sum": "$total"},
                    "order_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_spent": -1}},
            {"$limit": limit}
        ]

        return await Order.aaggregate(pipeline)

Indexing
--------

Create indexes for query optimization:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo import ASCENDING, DESCENDING

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        email: str
        name: str
        created_at: datetime

    # Create indexes on startup
    async def create_indexes():
        collection = await User.get_async_collection()

        # Unique email index
        await collection.create_index(
            [("email", ASCENDING)],
            unique=True
        )

        # Compound index for sorting
        await collection.create_index([
            ("created_at", DESCENDING),
            ("name", ASCENDING)
        ])

        # Text search index
        await collection.create_index([("name", "text")])

    # Use in FastAPI startup
    @app.on_event("startup")
    async def startup():
        await create_indexes()

Soft Delete Pattern
-------------------

Implement soft deletes instead of permanent deletion:

.. code-block:: python

    from lightodm import MongoBaseModel
    from datetime import datetime
    from typing import Optional

    class SoftDeleteModel(MongoBaseModel):
        """Base model with soft delete support"""
        deleted_at: Optional[datetime] = None

        async def soft_delete(self):
            """Mark as deleted instead of removing"""
            self.deleted_at = datetime.now()
            await self.asave()

        @classmethod
        async def find_active(cls, filter: dict = None, **kwargs):
            """Find only non-deleted documents"""
            filter = filter or {}
            filter["deleted_at"] = None
            return await cls.afind(filter, **kwargs)

        @classmethod
        async def find_deleted(cls, filter: dict = None, **kwargs):
            """Find only deleted documents"""
            filter = filter or {}
            filter["deleted_at"] = {"$ne": None}
            return await cls.afind(filter, **kwargs)

    class User(SoftDeleteModel):
        class Settings:
            name = "users"

        name: str
        email: str

    # Usage
    user = await User.aget(user_id)
    await user.soft_delete()  # Soft delete

    # Find only active users
    active_users = await User.find_active()

    # Find deleted users
    deleted_users = await User.find_deleted()

Validation and Hooks
--------------------

Add custom validation and pre/post save hooks:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pydantic import field_validator, model_validator
    from datetime import datetime
    import hashlib

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        email: str
        password_hash: str
        name: str
        created_at: datetime = Field(default_factory=datetime.now)
        updated_at: datetime = Field(default_factory=datetime.now)

        @field_validator("email")
        @classmethod
        def validate_email(cls, v: str) -> str:
            """Ensure email is lowercase"""
            return v.lower()

        @model_validator(mode="before")
        @classmethod
        def hash_password(cls, values):
            """Hash password if plain password provided"""
            if "password" in values:
                password = values.pop("password")
                values["password_hash"] = hashlib.sha256(
                    password.encode()
                ).hexdigest()
            return values

        async def asave(self, **kwargs):
            """Update timestamp before saving"""
            self.updated_at = datetime.now()
            return await super().asave(**kwargs)

    # Usage
    user = User(
        email="USER@EXAMPLE.COM",  # Will be lowercased
        password="secret123",  # Will be hashed
        name="John"
    )
    await user.asave()

Error Handling
--------------

Proper error handling for database operations:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo.errors import DuplicateKeyError, ConnectionFailure
    from fastapi import HTTPException

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        email: str
        name: str

    async def create_user_safe(email: str, name: str):
        """Create user with error handling"""
        try:
            user = User(email=email, name=name)
            await user.asave()
            return user
        except DuplicateKeyError:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

Testing with Mock
-----------------

Test your models using mongomock:

.. code-block:: python

    import pytest
    import mongomock
    from lightodm import MongoBaseModel

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

    @pytest.fixture
    def mock_db():
        """Provide mock MongoDB for testing"""
        client = mongomock.MongoClient()
        return client.test_db

    @pytest.fixture
    def user_model(mock_db, monkeypatch):
        """Override User model to use mock collection"""
        monkeypatch.setattr(
            User,
            "get_collection",
            lambda: mock_db.users
        )
        return User

    def test_create_user(user_model):
        """Test user creation"""
        user = user_model(name="John", email="john@example.com")
        user.save()

        # Verify user was saved
        assert user.id is not None

        # Retrieve user
        found = user_model.get(user.id)
        assert found.name == "John"
        assert found.email == "john@example.com"

See the ``examples/`` directory in the repository for complete working examples.
