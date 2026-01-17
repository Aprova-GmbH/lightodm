"""
Basic usage example for LightODM

This example demonstrates both sync and async operations with LightODM.

Before running:
    export MONGO_URL="mongodb://localhost:27017"
    export MONGO_USER="your_user"
    export MONGO_PASSWORD="your_password"
    export MONGO_DB_NAME="test_db"
"""

import asyncio
from typing import Optional
from lightodm import MongoBaseModel


# Define a model
class User(MongoBaseModel):
    class Settings:
        name = "users"

    name: str
    email: str
    age: Optional[int] = None
    active: bool = True


def sync_example():
    """Synchronous operations example"""
    print("\n=== Synchronous Example ===\n")

    # Create and save
    user = User(name="John Doe", email="john@example.com", age=30)
    print(f"Created user with ID: {user.id}")
    user.save()
    print("User saved to MongoDB")

    # Retrieve by ID
    retrieved = User.get(user.id)
    if retrieved:
        print(f"Retrieved user: {retrieved.name} ({retrieved.email})")

    # Update
    User.update_one({"name": "John Doe"}, {"$set": {"age": 31}})
    print("Updated user age to 31")

    # Find
    users = User.find({"active": True})
    print(f"Found {len(users)} active users")

    # Count
    count = User.count({"age": {"$gte": 18}})
    print(f"Number of adult users: {count}")

    # Delete
    user.delete()
    print(f"Deleted user {user.id}")


async def async_example():
    """Asynchronous operations example"""
    print("\n=== Asynchronous Example ===\n")

    # Create and save
    user = User(name="Jane Doe", email="jane@example.com", age=25)
    print(f"Created user with ID: {user.id}")
    await user.asave()
    print("User saved to MongoDB")

    # Retrieve by ID
    retrieved = await User.aget(user.id)
    if retrieved:
        print(f"Retrieved user: {retrieved.name} ({retrieved.email})")

    # Update
    await User.aupdate_one({"name": "Jane Doe"}, {"$set": {"age": 26}})
    print("Updated user age to 26")

    # Find
    users = await User.afind({"active": True})
    print(f"Found {len(users)} active users")

    # Iterate over results (memory efficient)
    print("Iterating over users:")
    async for user in User.afind_iter({"active": True}):
        print(f"  - {user.name}")

    # Count
    count = await User.acount({"age": {"$gte": 18}})
    print(f"Number of adult users: {count}")

    # Bulk insert
    new_users = [
        User(name="Alice", email="alice@example.com", age=28),
        User(name="Bob", email="bob@example.com", age=35),
    ]
    ids = await User.ainsert_many(new_users)
    print(f"Bulk inserted {len(ids)} users")

    # Aggregation
    pipeline = [
        {"$group": {"_id": "$active", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = await User.aaggregate(pipeline)
    print(f"Aggregation results: {results}")

    # Clean up
    await user.adelete()
    await User.adelete_many({"name": {"$in": ["Alice", "Bob"]}})
    print("Cleaned up test data")


if __name__ == "__main__":
    # Run sync example
    try:
        sync_example()
    except Exception as e:
        print(f"Sync example error: {e}")

    # Run async example
    try:
        asyncio.run(async_example())
    except Exception as e:
        print(f"Async example error: {e}")
