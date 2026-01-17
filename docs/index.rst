lightodm - Lightweight MongoDB ODM
===================================

**lightodm** is a minimalistic MongoDB ODM (Object-Document Mapper) for Python, designed as a lightweight alternative to Beanie.

Why lightodm?
-------------

* 🪶 **Lightweight**: ~500 lines of code vs 5000+ in Beanie
* 🔄 **Dual Support**: Both sync (PyMongo) and async (Motor) operations
* 🎯 **Pydantic v2 Native**: Built for Pydantic v2 from the ground up
* 🔌 **Flexible Connection**: Bring Your Own Connection (BYOC) pattern
* 📦 **Direct Access**: Direct PyMongo/Motor API access, no abstraction layers
* 💡 **Type Safe**: Full type hints support
* ✅ **Well Tested**: Comprehensive test coverage

Quick Start
-----------

Installation:

.. code-block:: bash

    pip install lightodm

Basic Usage:

.. code-block:: python

    from lightodm import MongoBaseModel, connect

    # Optional: Use built-in connection manager
    connect(
        url="mongodb://localhost:27017",
        username="user",
        password="pass",
        db_name="mydb"
    )

    # Define your model
    class User(MongoBaseModel):
        class Settings:
            name = "users"  # Collection name

        name: str
        email: str
        age: int

    # Sync operations
    user = User(name="John", email="john@example.com", age=30)
    user.save()
    found_user = User.get(user.id)

    # Async operations
    await user.asave()
    found_user = await User.aget(user.id)

Contents
--------

.. toctree::
   :maxdepth: 2

   quickstart
   api
   beanie_comparison
   examples

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
