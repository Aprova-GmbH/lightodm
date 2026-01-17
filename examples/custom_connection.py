"""
Custom connection example for LightODM

This example shows how to override the connection methods for custom logic.
"""

from typing import Optional
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from lightodm import MongoBaseModel


class CustomUser(MongoBaseModel):
    """
    User model with custom connection logic.

    Instead of using the singleton connection, this model
    uses its own custom connection methods.
    """

    class Settings:
        name = "custom_users"

    name: str
    email: str
    age: Optional[int] = None

    @classmethod
    def get_collection(cls):
        """Custom sync connection"""
        # Connect to a different database or with different settings
        client = MongoClient(
            "mongodb://localhost:27017",
            username="custom_user",
            password="custom_password"
        )
        db = client["custom_database"]
        return db["custom_users"]

    @classmethod
    async def get_async_collection(cls):
        """Custom async connection"""
        # Connect to a different database or with different settings
        client = AsyncIOMotorClient(
            "mongodb://localhost:27017",
            username="custom_user",
            password="custom_password"
        )
        db = client["custom_database"]
        return db["custom_users"]


# Usage remains the same
def main():
    # Sync
    user = CustomUser(name="Custom User", email="custom@example.com")
    user.save()

    # Async
    # await user.asave()


if __name__ == "__main__":
    main()
