"""
MongoDB Connection Manager

Thread-safe singleton connection manager for MongoDB supporting both sync (pymongo)
and async (motor) clients with automatic cleanup.
"""

import os
import atexit
import threading
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class MongoConnection:
    """
    Singleton MongoDB connection manager supporting both sync (pymongo)
    and async (motor) clients with thread-safety.

    The connection is configured via environment variables:
    - MONGO_URL: MongoDB connection URL
    - MONGO_USER: MongoDB username
    - MONGO_PASSWORD: MongoDB password
    - MONGO_DB_NAME: Database name

    Example:
        # Sync usage
        conn = MongoConnection()
        db = conn.database
        collection = conn.get_collection("users")

        # Async usage
        conn = MongoConnection()
        client = await conn.get_async_client()
        db = await conn.get_async_database()
    """

    _instance: Optional["MongoConnection"] = None
    _lock = threading.Lock()

    # Sync client
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    # Async client (motor)
    _async_client: Optional[AsyncIOMotorClient] = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Initialize sync client eagerly (to keep existing behavior)
        if self._client is None:
            self._initialize_connection()

    def _initialize_connection(self):
        """Initialize synchronous MongoDB connection"""
        mongo_url = os.environ.get("MONGO_URL")
        mongo_user = os.environ.get("MONGO_USER")
        mongo_password = os.environ.get("MONGO_PASSWORD")
        mongo_db_name = os.environ.get("MONGO_DB_NAME")

        if not all([mongo_url, mongo_user, mongo_password]):
            raise ValueError(
                "MongoDB connection parameters are not set. "
                "Please set MONGO_URL, MONGO_USER, and MONGO_PASSWORD environment variables."
            )

        try:
            self._client = MongoClient(
                mongo_url,
                username=mongo_user,
                password=mongo_password,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=20000,
                connectTimeoutMS=20000,
                heartbeatFrequencyMS=10000,
                retryWrites=True,
                retryReads=True,
                maxConnecting=2,
                waitQueueTimeoutMS=10000,
            )
            self._db = self._client[mongo_db_name] if mongo_db_name else self._client.get_default_database()
            # Test the connection
            self._client.admin.command("ping")
            atexit.register(self.close_connection)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize MongoDB (sync) connection: {e}")

    @property
    def client(self) -> MongoClient:
        """Get the synchronous MongoDB client"""
        if self._client is None:
            self._initialize_connection()
        return self._client

    @property
    def database(self) -> Database:
        """Get the synchronous MongoDB database"""
        if self._db is None:
            self._initialize_connection()
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a synchronous collection.

        Args:
            collection_name: Name of the collection

        Returns:
            PyMongo Collection instance
        """
        if self._db is None:
            self._initialize_connection()
        return self._db[collection_name]

    async def get_async_client(self) -> AsyncIOMotorClient:
        """
        Get or create the AsyncIOMotorClient and verify connectivity asynchronously.

        Returns:
            Motor AsyncIOMotorClient instance
        """
        if self._async_client is None:
            mongo_url = os.environ.get("MONGO_URL")
            mongo_user = os.environ.get("MONGO_USER")
            mongo_password = os.environ.get("MONGO_PASSWORD")

            if not all([mongo_url, mongo_user, mongo_password]):
                raise ValueError(
                    "MongoDB connection parameters are not set. "
                    "Please set MONGO_URL, MONGO_USER, and MONGO_PASSWORD environment variables."
                )

            try:
                # Create motor client lazily
                self._async_client = AsyncIOMotorClient(
                    mongo_url,
                    username=mongo_user,
                    password=mongo_password,
                )
                # Perform an async ping to ensure connectivity
                await self._async_client.admin.command("ping")
            except Exception as e:
                # Ensure no half-initialized client remains
                if self._async_client is not None:
                    self._async_client.close()
                self._async_client = None
                raise ConnectionError(f"Failed to initialize MongoDB (async) connection: {e}")

        return self._async_client

    async def get_async_database(self, db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
        """
        Get the asynchronous MongoDB database.

        Args:
            db_name: Optional database name override

        Returns:
            Motor AsyncIOMotorDatabase instance
        """
        client = await self.get_async_client()
        if db_name:
            return client[db_name]

        mongo_db_name = os.environ.get("MONGO_DB_NAME")
        if not mongo_db_name:
            return client.get_default_database()
        return client[mongo_db_name]

    def close_connection(self):
        """Close both sync and async clients if present."""
        # Close sync client
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            finally:
                self._client = None
                self._db = None

        # Close async client
        if self._async_client:
            try:
                # Motor's close is synchronous method
                self._async_client.close()
            except Exception:
                pass
            finally:
                self._async_client = None


# Global connection instance
_mongo_conn: Optional[MongoConnection] = None


def get_mongo_connection() -> MongoConnection:
    """
    Get the singleton MongoConnection instance.

    Returns:
        MongoConnection singleton
    """
    global _mongo_conn
    if _mongo_conn is None:
        _mongo_conn = MongoConnection()
    return _mongo_conn


def get_collection(collection_name: str) -> Collection:
    """
    Get a MongoDB collection by name using the singleton connection (sync).

    Args:
        collection_name: Name of the collection

    Returns:
        PyMongo Collection instance
    """
    conn = get_mongo_connection()
    return conn.get_collection(collection_name)


async def get_async_database(db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
    """
    Get asynchronous MongoDB database using the singleton connection.

    Args:
        db_name: Optional database name override

    Returns:
        Motor AsyncIOMotorDatabase instance
    """
    conn = get_mongo_connection()
    return await conn.get_async_database(db_name)


def get_database() -> Database:
    """
    Get synchronous MongoDB database using the singleton connection.

    Returns:
        PyMongo Database instance
    """
    conn = get_mongo_connection()
    return conn.database


def get_client() -> MongoClient:
    """
    Get synchronous MongoDB client using the singleton connection.

    Returns:
        PyMongo MongoClient instance
    """
    conn = get_mongo_connection()
    return conn.client


async def get_async_client() -> AsyncIOMotorClient:
    """
    Get asynchronous MongoDB client using the singleton connection.

    Returns:
        Motor AsyncIOMotorClient instance
    """
    conn = get_mongo_connection()
    return await conn.get_async_client()


def connect(
    url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    db_name: Optional[str] = None,
) -> Database:
    """
    Initialize MongoDB connection with optional explicit parameters.

    If parameters are not provided, they will be read from environment variables:
    - MONGO_URL
    - MONGO_USER
    - MONGO_PASSWORD
    - MONGO_DB_NAME

    Args:
        url: MongoDB connection URL (optional)
        username: MongoDB username (optional)
        password: MongoDB password (optional)
        db_name: Database name (optional)

    Returns:
        PyMongo Database instance

    Example:
        # Connect with explicit parameters
        db = connect(
            url="mongodb://localhost:27017",
            username="myuser",
            password="mypass",
            db_name="mydb"
        )

        # Or use environment variables
        db = connect()
    """
    # Set environment variables if provided
    if url:
        os.environ["MONGO_URL"] = url
    if username:
        os.environ["MONGO_USER"] = username
    if password:
        os.environ["MONGO_PASSWORD"] = password
    if db_name:
        os.environ["MONGO_DB_NAME"] = db_name

    # Initialize connection and return database
    return get_database()
