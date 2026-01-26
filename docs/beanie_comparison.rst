LightODM vs Beanie
==================

This page compares LightODM with `Beanie <https://github.com/roman-right/beanie>`_, a popular MongoDB ODM for Python.

Quick Comparison
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - LightODM
     - Beanie
   * - **Code Size**
     - ~500 lines
     - ~5000+ lines
   * - **Pydantic**
     - v2 native
     - v1 compatibility layer
   * - **Sync Support**
     - ✅ Yes (PyMongo)
     - ❌ No (async only)
   * - **Async Support**
     - ✅ Yes (Motor)
     - ✅ Yes (Motor)
   * - **Dependencies**
     - 3 (pydantic, pymongo, motor)
     - Many (including extra features)
   * - **Connection Pattern**
     - BYOC (Bring Your Own Connection)
     - Opinionated initialization
   * - **Direct DB Access**
     - ✅ Full PyMongo/Motor access
     - Abstracted through Beanie API
   * - **Learning Curve**
     - Minimal (if you know PyMongo)
     - Moderate (learn Beanie abstractions)
   * - **Query Builder**
     - Use MongoDB query syntax directly
     - Beanie's fluent query API
   * - **Migrations**
     - DIY with PyMongo
     - Built-in migration tools
   * - **Validation**
     - Pydantic v2
     - Pydantic v1/v2
   * - **Relationships**
     - Manual (via refs)
     - Built-in Link/BackLink
   * - **Caching**
     - DIY
     - Optional built-in caching
   * - **Best For**
     - Simple projects, sync+async, full control
     - Complex projects, async-only, feature-rich

Philosophy
----------

**LightODM**: Minimalistic wrapper
  LightODM is a thin layer over PyMongo/Motor that adds Pydantic validation and convenience methods. You still write MongoDB queries directly.

**Beanie**: Full-featured ODM
  Beanie is a comprehensive ODM with its own query language, migrations, relationships, and many additional features.

When to Choose LightODM
------------------------

Choose LightODM if you:

1. **Need both sync and async**

   LightODM supports both paradigms with the same model:

   .. code-block:: python

       # Sync
       user.save()
       users = User.find({})

       # Async
       await user.asave()
       users = await User.afind({})

   Beanie is async-only.

2. **Prefer MongoDB's native query syntax**

   LightODM uses MongoDB queries directly:

   .. code-block:: python

       # LightODM - standard MongoDB syntax
       User.find({"age": {"$gte": 18}, "city": "NYC"})

   vs Beanie's query builder:

   .. code-block:: python

       # Beanie - custom query API
       await User.find(User.age >= 18, User.city == "NYC").to_list()

3. **Want minimal dependencies**

   LightODM has only 3 dependencies. Beanie has more for its extra features.

4. **Need direct PyMongo/Motor access**

   With LightODM, you get the actual collection object:

   .. code-block:: python

       collection = User.get_collection()  # PyMongo Collection
       collection.create_index([("email", 1)], unique=True)

5. **Prefer simplicity over features**

   LightODM's entire codebase is ~500 lines. Easy to understand and debug.

When to Choose Beanie
----------------------

Choose Beanie if you:

1. **Only use async/await**

   If your app is fully async and you don't need sync support, Beanie is a great choice.

2. **Want built-in relationships**

   Beanie has ``Link`` and ``BackLink`` for document relationships:

   .. code-block:: python

       class User(Document):
           name: str

       class Post(Document):
           title: str
           author: Link[User]  # Automatic relationship handling

   LightODM requires manual reference management.

3. **Need migration tools**

   Beanie has built-in migration support for schema changes.

4. **Prefer fluent query API**

   Some developers prefer Beanie's Pythonic query syntax over raw MongoDB queries.

5. **Want additional features**

   Beanie includes caching, event hooks, custom types, and more out of the box.

Code Comparison
---------------

Basic Model Definition
~~~~~~~~~~~~~~~~~~~~~~~

**LightODM**:

.. code-block:: python

    from lightodm import MongoBaseModel
    from typing import Optional

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str
        age: Optional[int] = None

**Beanie**:

.. code-block:: python

    from beanie import Document
    from typing import Optional

    class User(Document):
        name: str
        email: str
        age: Optional[int] = None

        class Settings:
            name = "users"

Very similar! The main difference is the base class.

Initialization
~~~~~~~~~~~~~~

**LightODM** - Simple connection:

.. code-block:: python

    from lightodm import connect

    connect(
        url="mongodb://localhost:27017",
        db_name="mydb"
    )

**LightODM** - Custom connection (BYOC):

.. code-block:: python

    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client.mydb

    class User(MongoBaseModel):
        @classmethod
        def get_collection(cls):
            return db.users

**Beanie** - Requires initialization:

.. code-block:: python

    from beanie import init_beanie
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://localhost:27017")

    await init_beanie(
        database=client.mydb,
        document_models=[User, Post, Comment]
    )

Beanie requires listing all models upfront.

CRUD Operations
~~~~~~~~~~~~~~~

**LightODM**:

.. code-block:: python

    # Create & Save (sync)
    user = User(name="John", email="john@example.com")
    user.save()

    # or async
    await user.asave()

    # Find (sync)
    users = User.find({"age": {"$gte": 18}})

    # or async
    users = await User.afind({"age": {"$gte": 18}})

    # Update (sync)
    User.update_one({"_id": user_id}, {"$set": {"age": 31}})

    # or async
    await User.aupdate_one({"_id": user_id}, {"$set": {"age": 31}})

**Beanie** (async only):

.. code-block:: python

    # Create & Save
    user = User(name="John", email="john@example.com")
    await user.insert()

    # Find
    users = await User.find(User.age >= 18).to_list()

    # Update
    await user.set({User.age: 31})

Complex Queries
~~~~~~~~~~~~~~~

**LightODM** - Use MongoDB aggregation directly:

.. code-block:: python

    pipeline = [
        {"$match": {"age": {"$gte": 18}}},
        {"$group": {
            "_id": "$city",
            "count": {"$sum": 1},
            "avg_age": {"$avg": "$age"}
        }}
    ]

    results = User.aggregate(pipeline)
    # or
    results = await User.aaggregate(pipeline)

**Beanie** - Use aggregation API:

.. code-block:: python

    results = await User.find(User.age >= 18).aggregate([
        {"$group": {
            "_id": "$city",
            "count": {"$sum": 1},
            "avg_age": {"$avg": "$age"}
        }}
    ]).to_list()

Both support MongoDB's powerful aggregation framework.

Relationships
~~~~~~~~~~~~~

**LightODM** - Manual references:

.. code-block:: python

    class Post(MongoBaseModel):
        class Settings:
            name = "posts"

        title: str
        author_id: str  # Manual reference

        def get_author(self):
            return User.get(self.author_id)

        async def aget_author(self):
            return await User.aget(self.author_id)

**Beanie** - Built-in Links:

.. code-block:: python

    from beanie import Document, Link

    class Post(Document):
        title: str
        author: Link[User]  # Automatic reference

    # Fetch with relationship
    post = await Post.find_one(Post.title == "Hello").fetch_links()
    print(post.author.name)  # Automatically loaded

Beanie's ``Link`` is more convenient but adds abstraction.

Migrations
----------

**LightODM**:

No built-in migration support. Use PyMongo directly:

.. code-block:: python

    from lightodm import get_db

    db = get_db()

    # Add field to all users
    db.users.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "active"}}
    )

**Beanie**:

Built-in migration framework:

.. code-block:: python

    from beanie import Document, iterative_migration

    @iterative_migration()
    class User(Document):
        name: str
        status: str = "active"  # New field

        class Settings:
            name = "users"

Beanie handles migrations automatically.

Migration from Beanie
---------------------

Migrating from Beanie to LightODM is straightforward:

1. **Change base class**:

   .. code-block:: python

       # Before (Beanie)
       from beanie import Document
       class User(Document):
           ...

       # After (LightODM)
       from lightodm import MongoBaseModel
       class User(MongoBaseModel):
           ...

2. **Update connection initialization**:

   .. code-block:: python

       # Before (Beanie)
       await init_beanie(database=db, document_models=[User])

       # After (LightODM)
       from lightodm import connect
       connect(db_name="mydb")

3. **Convert async-only methods to sync or async**:

   .. code-block:: python

       # Before (Beanie - async only)
       await user.insert()
       users = await User.find_all().to_list()

       # After (LightODM - choose sync or async)
       user.save()  # sync
       await user.asave()  # async

       users = User.find({})  # sync
       users = await User.afind({})  # async

4. **Replace query builder with MongoDB queries**:

   .. code-block:: python

       # Before (Beanie)
       users = await User.find(
           User.age >= 18,
           User.city == "NYC"
       ).to_list()

       # After (LightODM)
       users = User.find({"age": {"$gte": 18}, "city": "NYC"})
       # or async
       users = await User.afind({"age": {"$gte": 18}, "city": "NYC"})

5. **Handle relationships manually**:

   .. code-block:: python

       # Before (Beanie)
       class Post(Document):
           author: Link[User]

       post = await Post.find_one().fetch_links()
       print(post.author.name)

       # After (LightODM)
       class Post(MongoBaseModel):
           author_id: str

           async def get_author(self):
               return await User.aget(self.author_id)

       post = await Post.afind_one({})
       author = await post.get_author()
       print(author.name)

For a complete migration guide, see the ``MIGRATION_FROM_BEANIE.md`` file in the repository.

Performance
-----------

**LightODM** is slightly faster for simple operations due to less abstraction overhead.

**Beanie** may be faster for complex relationship queries with ``fetch_links()`` optimization.

For most applications, the performance difference is negligible. Choose based on features and developer experience.

Conclusion
----------

**Choose LightODM** for:
  - Sync + async support
  - Minimal dependencies
  - Direct MongoDB control
  - Simple projects
  - Learning MongoDB

**Choose Beanie** for:
  - Async-only applications
  - Built-in relationships
  - Migration tools
  - Feature-rich ODM
  - Complex domain models

Both are excellent tools. LightODM prioritizes simplicity and control, while Beanie provides a comprehensive feature set.
