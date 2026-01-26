API Reference
=============

This page provides detailed documentation for all LightODM classes and functions.

Core Classes
------------

MongoBaseModel
~~~~~~~~~~~~~~

.. autoclass:: lightodm.MongoBaseModel
   :show-inheritance:

   Base class for MongoDB document models with ODM functionality.

   **Settings Class**

   Every model must define an inner ``Settings`` class with the following attribute:

   .. attribute:: Settings.name
      :type: str

      MongoDB collection name for this model.

   **Field Mapping**

   .. attribute:: id
      :type: Optional[str]

      Document ID that maps to MongoDB ``_id`` field. Auto-generated using ObjectId if not provided.

   **Synchronous CRUD Methods**

   .. automethod:: save
   .. automethod:: delete
   .. automethod:: get
   .. automethod:: find_one
   .. automethod:: find
   .. automethod:: find_iter
   .. automethod:: count
   .. automethod:: update_one
   .. automethod:: update_many
   .. automethod:: delete_one
   .. automethod:: delete_many
   .. automethod:: aggregate
   .. automethod:: insert_many

   **Asynchronous CRUD Methods**

   .. automethod:: asave
   .. automethod:: adelete
   .. automethod:: aget
   .. automethod:: afind_one
   .. automethod:: afind
   .. automethod:: afind_iter
   .. automethod:: acount
   .. automethod:: aupdate_one
   .. automethod:: aupdate_many
   .. automethod:: adelete_one
   .. automethod:: adelete_many
   .. automethod:: aaggregate
   .. automethod:: ainsert_many

   **Collection Access Methods**

   .. automethod:: get_collection
   .. automethod:: get_async_collection

   **Internal Methods**

   .. automethod:: _to_mongo_dict
   .. automethod:: _from_mongo_dict
   .. automethod:: _get_collection_name
   .. automethod:: _validate_collection_name

Connection Management
---------------------

MongoConnection
~~~~~~~~~~~~~~~

.. autoclass:: lightodm.MongoConnection
   :show-inheritance:

   Singleton MongoDB connection manager supporting both sync and async clients.

   **Properties**

   .. autoproperty:: client
   .. autoproperty:: database

   **Methods**

   .. automethod:: get_collection
   .. automethod:: get_async_client
   .. automethod:: get_async_database
   .. automethod:: close_connection

Helper Functions
----------------

connect()
~~~~~~~~~

.. autofunction:: lightodm.connect

   Convenience function to initialize MongoDB connection with the singleton pattern.

   :param url: MongoDB connection URL (e.g., ``mongodb://localhost:27017``)
   :type url: str, optional
   :param username: MongoDB username
   :type username: str, optional
   :param password: MongoDB password
   :type password: str, optional
   :param db_name: Default database name
   :type db_name: str, optional
   :return: MongoDB database instance
   :rtype: pymongo.database.Database

   **Environment Variables**

   If parameters are not provided, the function will attempt to read from environment variables:

   - ``MONGO_URL``: MongoDB connection URL
   - ``MONGO_USER``: MongoDB username
   - ``MONGO_PASSWORD``: MongoDB password
   - ``MONGO_DB_NAME``: Default database name

   **Example**

   .. code-block:: python

       from lightodm import connect, MongoBaseModel

       # Connect explicitly
       connect(
           url="mongodb://localhost:27017",
           username="myuser",
           password="mypass",
           db_name="mydb"
       )

       # Or using environment variables
       # MONGO_URL=mongodb://localhost:27017
       # MONGO_USER=myuser
       # MONGO_PASSWORD=mypass
       # MONGO_DB_NAME=mydb
       connect()

generate_id()
~~~~~~~~~~~~~

.. autofunction:: lightodm.generate_id

   Generate a unique ID for MongoDB documents.

   :param \\**kwargs: Optional keyword arguments to generate deterministic hash-based ID
   :type \\**kwargs: dict
   :return: Unique ID string (ObjectId or MD5 hash)
   :rtype: str

   **Behavior**

   - If called without arguments: Returns a new ObjectId string
   - If called with keyword arguments: Returns MD5 hash of sorted key-value pairs (deterministic)

   **Example**

   .. code-block:: python

       from lightodm import generate_id

       # Random ObjectId
       id1 = generate_id()  # '507f1f77bcf86cd799439011'

       # Deterministic hash-based ID
       id2 = generate_id(user_id="123", type="profile")
       id3 = generate_id(type="profile", user_id="123")
       assert id2 == id3  # Same hash for same inputs

Type Definitions
----------------

Collection Types
~~~~~~~~~~~~~~~~

LightODM uses the following collection types from PyMongo and Motor:

.. py:currentmodule:: pymongo.collection

.. py:class:: Collection

   Synchronous MongoDB collection (from PyMongo).

.. py:currentmodule:: motor.motor_asyncio

.. py:class:: AsyncIOMotorCollection

   Asynchronous MongoDB collection (from Motor).

.. py:currentmodule:: lightodm

TypeVar
~~~~~~~

.. py:data:: T
   :type: TypeVar

   Type variable bound to ``MongoBaseModel`` for generic class methods.

   Used internally for type hinting to ensure methods return instances of the correct model class.

Configuration
-------------

Model Configuration
~~~~~~~~~~~~~~~~~~~

LightODM models use Pydantic v2's ``model_config`` with the following settings:

.. code-block:: python

    from pydantic import ConfigDict

    model_config = ConfigDict(
        populate_by_name=True,  # Allow field population by alias
        extra='allow'           # Allow extra fields beyond model definition
    )

**populate_by_name**
  Enables using either the field name or alias (``_id`` / ``id``) when creating models.

**extra='allow'**
  Allows storing arbitrary extra fields on the model. Extra fields are preserved when saving to MongoDB.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The following environment variables are recognized by ``MongoConnection`` and ``connect()``:

.. envvar:: MONGO_URL

   MongoDB connection URL.

   Example: ``mongodb://localhost:27017``

.. envvar:: MONGO_USER

   MongoDB username for authentication.

.. envvar:: MONGO_PASSWORD

   MongoDB password for authentication.

.. envvar:: MONGO_DB_NAME

   Default database name to use.

Exceptions
----------

LightODM raises the following exceptions:

NotImplementedError
~~~~~~~~~~~~~~~~~~~

Raised when:

- A model doesn't define a ``Settings`` class
- ``Settings.name`` is not defined
- ``get_collection()`` or ``get_async_collection()`` is not implemented

ValueError
~~~~~~~~~~

Raised when:

- Attempting to save a document without an ID
- MongoDB connection parameters are missing

PyMongo Exceptions
~~~~~~~~~~~~~~~~~~

LightODM also propagates exceptions from PyMongo and Motor. Common ones include:

- ``pymongo.errors.ConnectionFailure``: Cannot connect to MongoDB
- ``pymongo.errors.OperationFailure``: MongoDB operation failed
- ``pymongo.errors.DuplicateKeyError``: Unique constraint violation

See `PyMongo documentation <https://pymongo.readthedocs.io/>`_ for complete exception reference.

Usage Patterns
--------------

Bring Your Own Connection (BYOC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For advanced use cases, override collection methods to use custom connection logic:

.. code-block:: python

    from lightodm import MongoBaseModel
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient

    # Global connection instances
    sync_client = MongoClient("mongodb://localhost:27017")
    async_client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_name = "myapp"

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str
        email: str

        @classmethod
        def get_collection(cls):
            return sync_client[db_name][cls.Settings.name]

        @classmethod
        async def get_async_collection(cls):
            return async_client[db_name][cls.Settings.name]

Thread Safety
~~~~~~~~~~~~~

``MongoConnection`` is thread-safe and uses a singleton pattern with locking:

.. code-block:: python

    from concurrent.futures import ThreadPoolExecutor
    from lightodm import connect, MongoBaseModel

    connect()  # Initialize once

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str

    def save_user(i):
        user = User(name=f"User {i}")
        user.save()

    # Safe to use from multiple threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(save_user, range(100))

Async Context
~~~~~~~~~~~~~

Always use async methods in async contexts:

.. code-block:: python

    import asyncio
    from lightodm import MongoBaseModel

    class User(MongoBaseModel):
        class Settings:
            name = "users"

        name: str

    async def main():
        # Use async methods
        user = User(name="Async User")
        await user.asave()

        users = await User.afind({})

        async for user in User.afind_iter({}):
            print(user.name)

    asyncio.run(main())
