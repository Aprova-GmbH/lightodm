Quick Start Guide
=================

Installation
------------

Install LightODM using pip:

.. code-block:: bash

    pip install lightodm

Basic Requirements
------------------

LightODM requires:

- Python 3.11+
- MongoDB 4.0+ (local or remote)
- Pydantic v2

Connection Setup
----------------

Simple Connection (Recommended for Getting Started)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the built-in ``connect()`` helper for simple applications:

.. code-block:: python

    from lightodm import connect, MongoBaseModel

    # Connect using environment variables or explicit parameters
    connect(
        url="mongodb://localhost:27017",
        username="your_username",
        password="your_password",
        db_name="your_database"
    )

    # Or using environment variables:
    # MONGO_URL=mongodb://localhost:27017
    # MONGO_USER=your_username
    # MONGO_PASSWORD=your_password
    # MONGO_DB_NAME=your_database
    # Then just call: connect()


Custom Connection (Advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more control, override the ``get_collection()`` and ``get_async_collection()`` methods:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient

    # Your custom connection logic
    client = MongoClient("mongodb://localhost:27017")
    db = client.your_database

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

        @classmethod
        def get_collection(cls):
            return db[cls.Settings.name]

        @classmethod
        async def get_async_collection(cls):
            # Your async client logic
            pass

Defining Models
---------------

Create a model by subclassing ``MongoBaseModel``:

.. code-block:: python

    from typing import Optional
    from lightodm import MongoBaseModel

    class User(MongoBaseModel):
        class Settings:
            name = "users"  # MongoDB collection name

        name: str
        email: str
        age: Optional[int] = None

Key points:

- Every model must have a ``Settings`` class with a ``name`` attribute
- The ``id`` field is automatically generated (maps to MongoDB ``_id``)
- Use Pydantic field types for validation
- Optional fields default to ``None``

Synchronous CRUD Operations
----------------------------

Create and Save
~~~~~~~~~~~~~~~

.. code-block:: python

    # Create a new user
    user = User(name="John Doe", email="john@example.com", age=30)

    # Save to database (upsert)
    user.save()
    print(f"Saved user with ID: {user.id}")

    # Save with exclude_none to skip None values
    user = User(name="Jane Doe", email="jane@example.com")
    user.save(exclude_none=True)  # age won't be saved

Retrieve
~~~~~~~~

.. code-block:: python

    # Get by ID
    user = User.get("507f1f77bcf86cd799439011")

    if user:
        print(f"Found: {user.name}")
    else:
        print("User not found")

    # Find one by filter
    user = User.find_one({"email": "john@example.com"})

    # Find multiple users
    users = User.find({"age": {"$gte": 18}})

    for user in users:
        print(f"{user.name} is {user.age} years old")

    # Find with pagination
    users = User.find({}, skip=10, limit=5)

    # Find with sorting
    users = User.find({}, sort=[("age", -1)])  # Descending by age

Update
~~~~~~

.. code-block:: python

    # Update instance and save
    user = User.get(user_id)
    user.age = 31
    user.save()

    # Update one document
    User.update_one(
        {"_id": user_id},
        {"$set": {"age": 31}}
    )

    # Update many documents
    count = User.update_many(
        {"age": {"$lt": 18}},
        {"$set": {"minor": True}}
    )
    print(f"Updated {count} users")

    # Upsert
    User.update_one(
        {"email": "new@example.com"},
        {"$set": {"name": "New User"}},
        upsert=True
    )

Delete
~~~~~~

.. code-block:: python

    # Delete instance
    user = User.get(user_id)
    user.delete()

    # Delete one by filter
    deleted = User.delete_one({"email": "old@example.com"})

    # Delete many
    count = User.delete_many({"age": {"$lt": 18}})
    print(f"Deleted {count} users")

Count
~~~~~

.. code-block:: python

    # Count all
    total = User.count()
    print(f"Total users: {total}")

    # Count with filter
    adults = User.count({"age": {"$gte": 18}})
    print(f"Adult users: {adults}")

Asynchronous Operations
------------------------

LightODM provides async versions of all CRUD operations with the ``a`` prefix:

.. code-block:: python

    import asyncio
    from lightodm import MongoBaseModel

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

    async def main():
        # Create and save
        user = User(name="Async User", email="async@example.com")
        await user.asave()

        # Retrieve
        user = await User.aget(user.id)

        # Find
        users = await User.afind({"email": {"$regex": "@example.com"}})

        # Find one
        user = await User.afind_one({"name": "Async User"})

        # Update
        await User.aupdate_one(
            {"_id": user.id},
            {"$set": {"name": "Updated User"}}
        )

        # Delete
        await user.adelete()

        # Count
        count = await User.acount()

    # Run async code
    asyncio.run(main())

Async Iteration
~~~~~~~~~~~~~~~~

For large result sets, use async iteration to avoid loading all documents into memory:

.. code-block:: python

    async def process_users():
        async for user in User.afind_iter({}):
            print(f"Processing {user.name}")
            # Process user without loading entire collection

Aggregation
-----------

Both sync and async aggregation are supported:

.. code-block:: python

    # Synchronous aggregation
    pipeline = [
        {"$match": {"age": {"$gte": 18}}},
        {"$group": {
            "_id": "$city",
            "count": {"$sum": 1},
            "avg_age": {"$avg": "$age"}
        }},
        {"$sort": {"count": -1}}
    ]

    results = User.aggregate(pipeline)
    for result in results:
        print(f"{result['_id']}: {result['count']} users")

    # Asynchronous aggregation
    async def get_stats():
        results = await User.aaggregate(pipeline)
        return results

Bulk Operations
---------------

Insert Many
~~~~~~~~~~~

.. code-block:: python

    users = [
        User(name=f"User {i}", email=f"user{i}@example.com")
        for i in range(100)
    ]

    # Synchronous
    ids = User.insert_many(users)
    print(f"Inserted {len(ids)} users")

    # Asynchronous
    ids = await User.ainsert_many(users)

Working with Extra Fields
--------------------------

LightODM allows extra fields beyond the model definition:

.. code-block:: python

    # Create user with extra field
    user = User(
        name="John",
        email="john@example.com",
        custom_field="custom_value"
    )

    # Extra fields are preserved
    user.save()

    # Extra fields are in the document
    doc = user._to_mongo_dict()
    assert doc["custom_field"] == "custom_value"

    # Retrieve and access extra fields
    loaded_user = User.get(user.id)
    extra_value = loaded_user.__pydantic_extra__.get("custom_field")

Next Steps
----------

- See :doc:`examples` for real-world usage patterns
- Read :doc:`api` for complete API reference
- Check :doc:`beanie_comparison` for migration from Beanie
